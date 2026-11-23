#!/usr/bin/env python3
"""Translate a catalog rule's `assert` expression into SQL and Java.

Catalog v2 carries 607 Shariah and arithmetic invariants as expressions.  This
module translates the ones that fall inside a deliberately SMALL grammar and
REFUSES the rest, so the generator never approximates an invariant it cannot
express.  A refused rule is emitted as UNIMPLEMENTED in the generated registry
and listed in the repo's docs/RULES-GAPS.md — reported, never dropped and never
silently claimed.

THE GRAMMAR (everything else is out, on purpose)

    expr        := implication
    implication := or ( ('->' | 'implies') implication )?    A -> B == !A || B
    or          := and ( '||' and )*
    and         := cmp ( '&&' cmp )*
    cmp         := add ( ('=='|'!='|'<='|'>='|'<'|'>') add )?
                 | add ('in' | 'not' 'in') '[' literal (',' literal)* ']'
                 | add 'is' ('not')? 'null'                 -- present/absent
    add         := mul ( ('+'|'-') mul )*
    mul         := unary ( '*' unary )*
    unary       := '!' unary | primary
    primary     := '(' expr ')' | call | literal | field
    call        := ('present'|'absent'|'isSet'|'exists'|'hasField') '(' field ')'
                 | 'implies' '(' expr ',' expr ')'      -- same node as A -> B
                 | 'not' '(' expr ')'                   -- same node as !A
    literal     := '...' | "..." | int | true | false | null
    field       := a control-record field name, optionally written `cr.<name>`
                   (the governance fragment's spelling), and nothing else

EVERY identifier must resolve to a field of the control record being generated.
That one rule is what makes the translation safe: `count(bq.psr where …)`,
`sum(...)`, `forall(...)`, `immutable(...)`, `appendOnly(...)` and any `bq.`
path all fail it, so they are refused rather than mis-translated.

Fields of type ratio / period / array are also refused: a ratio is two columns
(numerator, denominator) and comparing it needs cross-multiplication, which
this grammar has no term for.  Those rules are reported as gaps.

NULL SEMANTICS, stated because it differs between the two targets:
  - SQL: a CHECK whose expression is UNKNOWN passes.  Required fields are
    NOT NULL, so for them the check always bites; for an optional field the
    check bites only when a value is present.  That is Postgres, not a choice.
  - Java: the generated method returns NOT_APPLICABLE when any field it reads
    is null, rather than guessing.  The two targets therefore agree.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field

PRESENCE_CALLS = {"present", "isset", "exists", "hasfield"}
ABSENCE_CALLS = {"absent"}

# Java/SQL type class per catalog field type.
TYPE_CLASS = {
    "id": "string", "ref": "string", "string": "string", "enum": "string",
    "currency": "string", "countryCode": "string",
    "bool": "bool", "int32": "long", "int64": "long", "money": "long",
    "date": "temporal", "timestamp": "temporal",
    "ratio": "unsupported", "period": "unsupported", "array": "unsupported",
}

JAVA_TYPE = {
    "id": "String", "ref": "String", "string": "String", "enum": "String",
    "currency": "String", "countryCode": "String",
    "bool": "Boolean", "int32": "Integer", "int64": "Long", "money": "Long",
    "date": "java.time.LocalDate", "timestamp": "java.time.OffsetDateTime",
}


class Untranslatable(Exception):
    """The expression is outside the grammar. Carries the human reason."""


# ------------------------------------------------------------------- tokeniser

TOKEN_RE = re.compile(r"""
    \s*(?:
        (?P<str>'[^']*'|"[^"]*")
      | (?P<int>-?\d+)
      | (?P<op>->|==|!=|<=|>=|&&|\|\||[()\[\],+\-*<>!])
      | (?P<ident>[A-Za-z_][A-Za-z0-9_.]*)
      | (?P<bad>\S)
    )
""", re.VERBOSE)


@dataclass
class Tok:
    kind: str
    text: str


def tokenise(src: str) -> list[Tok]:
    toks, pos = [], 0
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        if m.group("bad"):
            raise Untranslatable(f"unexpected character {m.group('bad')!r}")
        for kind in ("str", "int", "op", "ident"):
            if m.group(kind):
                toks.append(Tok(kind, m.group(kind)))
                break
    return toks


# ----------------------------------------------------------------------- AST

@dataclass
class Node:
    kind: str                      # lit | field | not | bin | impl | call | in
    text: str = ""
    children: list = dc_field(default_factory=list)
    lit_type: str = ""             # for lit: string | long | bool | null


class Parser:
    def __init__(self, toks: list[Tok]):
        self.toks, self.i = toks, 0

    def peek(self) -> Tok | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def eat(self, text: str | None = None) -> Tok:
        t = self.peek()
        if t is None:
            raise Untranslatable("expression ends early")
        if text is not None and t.text != text:
            raise Untranslatable(f"expected {text!r}, found {t.text!r}")
        self.i += 1
        return t

    def parse(self) -> Node:
        n = self.implication()
        if self.peek() is not None:
            raise Untranslatable(f"trailing {self.peek().text!r}")
        return n

    def implication(self) -> Node:
        left = self.or_()
        t = self.peek()
        if t and (t.text == "->" or (t.kind == "ident" and t.text == "implies")):
            self.eat()
            return Node("impl", "->", [left, self.implication()])
        return left

    def or_(self) -> Node:
        n = self.and_()
        while (t := self.peek()) and t.text == "||":
            self.eat()
            n = Node("bin", "||", [n, self.and_()])
        return n

    def and_(self) -> Node:
        n = self.cmp()
        while (t := self.peek()) and t.text == "&&":
            self.eat()
            n = Node("bin", "&&", [n, self.cmp()])
        return n

    def cmp(self) -> Node:
        left = self.add()
        t = self.peek()
        if t and t.kind == "ident" and t.text == "is":
            self.eat()
            negated = False
            if (t2 := self.peek()) and t2.kind == "ident" and t2.text == "not":
                self.eat()
                negated = True
            nx = self.eat()
            if nx.text.lower() != "null":
                raise Untranslatable("`is " + nx.text + "` is outside the grammar")
            if left.kind != "field":
                raise Untranslatable("`is null` applies to a field only")
            return Node("call", "present" if negated else "absent", [left])
        if t and t.kind == "ident" and t.text == "not" \
                and self.i + 1 < len(self.toks) and self.toks[self.i + 1].text == "in":
            self.eat(); self.eat()
            return Node("not", "!", [self._in_list(left)])
        if t and t.kind == "ident" and t.text == "in":
            self.eat()
            return self._in_list(left)
        if t and t.text in ("==", "!=", "<=", ">=", "<", ">"):
            self.eat()
            return Node("bin", t.text, [left, self.add()])
        return left

    def _in_list(self, left: Node) -> Node:
        self.eat("[")
        items = [self.primary()]
        while (t := self.peek()) and t.text == ",":
            self.eat()
            items.append(self.primary())
        self.eat("]")
        return Node("in", "in", [left, *items])

    def add(self) -> Node:
        n = self.mul()
        while (t := self.peek()) and t.text in ("+", "-"):
            self.eat()
            n = Node("bin", t.text, [n, self.mul()])
        return n

    def mul(self) -> Node:
        n = self.unary()
        while (t := self.peek()) and t.text == "*":
            self.eat()
            n = Node("bin", "*", [n, self.unary()])
        return n

    def unary(self) -> Node:
        t = self.peek()
        if t and t.text == "!":
            self.eat()
            return Node("not", "!", [self.unary()])
        if t and t.text == "-":
            self.eat()
            return Node("bin", "-", [Node("lit", "0", lit_type="long"), self.unary()])
        return self.primary()

    def primary(self) -> Node:
        t = self.eat()
        if t.text == "(":
            n = self.implication()
            self.eat(")")
            return n
        if t.kind == "str":
            return Node("lit", t.text[1:-1], lit_type="string")
        if t.kind == "int":
            return Node("lit", t.text, lit_type="long")
        if t.kind == "ident":
            low = t.text.lower()
            if low in ("true", "false"):
                return Node("lit", low, lit_type="bool")
            if low == "null":
                return Node("lit", "null", lit_type="null")
            if (nx := self.peek()) and nx.text == "(":
                # implies(A, B) and not(A) are spellings of -> and !, used by
                # four of the six fragments.  Same meaning, so same AST node.
                if low == "implies":
                    self.eat("(")
                    a = self.implication()
                    self.eat(",")
                    b = self.implication()
                    self.eat(")")
                    return Node("impl", "->", [a, b])
                if low == "not":
                    self.eat("(")
                    a = self.implication()
                    self.eat(")")
                    return Node("not", "!", [a])
                if low not in PRESENCE_CALLS | ABSENCE_CALLS:
                    raise Untranslatable(f"function {t.text}() is outside the grammar")
                self.eat("(")
                arg = self.eat()
                if arg.kind != "ident":
                    raise Untranslatable(f"{t.text}() takes a field name")
                self.eat(")")
                return Node("call", low, [Node("field", arg.text)])
            name = t.text
            if "." in name:
                # `cr.<field>` is the governance fragment's spelling for a
                # control-record field.  Any OTHER dotted path (bq.psr.x,
                # BoardCompositionPolicy.y) names something this service domain
                # does not own, so it is refused rather than guessed at.
                head, _, rest = name.partition(".")
                if head != "cr" or "." in rest:
                    raise Untranslatable("dotted path " + repr(name)
                                         + " is outside the control record")
                name = rest
            return Node("field", name)
        raise Untranslatable(f"unexpected token {t.text!r}")


# --------------------------------------------------------------- type checking

def field_class(name: str, fields: dict) -> str:
    fld = fields.get(name)
    if fld is None:
        raise Untranslatable(f"{name!r} is not a control-record field")
    cls = TYPE_CLASS.get(fld["type"], "unsupported")
    if cls == "unsupported":
        raise Untranslatable(f"field {name!r} is of type {fld['type']!r}, "
                             f"which this grammar cannot compare")
    return cls


def node_class(n: Node, fields: dict) -> str:
    """bool | long | string | temporal — raises Untranslatable on a mismatch."""
    if n.kind == "lit":
        return {"string": "string", "long": "long",
                "bool": "bool", "null": "null"}[n.lit_type]
    if n.kind == "field":
        return field_class(n.text, fields)
    if n.kind in ("not",):
        if node_class(n.children[0], fields) != "bool":
            raise Untranslatable("! applied to a non-boolean")
        return "bool"
    if n.kind in ("call", "impl"):
        if n.kind == "impl":
            for c in n.children:
                if node_class(c, fields) != "bool":
                    raise Untranslatable("-> applied to a non-boolean")
        else:
            field_class(n.children[0].text, fields)
        return "bool"
    if n.kind == "in":
        left = node_class(n.children[0], fields)
        for item in n.children[1:]:
            if node_class(item, fields) not in (left, "null"):
                raise Untranslatable("`in` list mixes types")
        return "bool"
    if n.kind == "bin":
        op = n.text
        a, b = (node_class(c, fields) for c in n.children)
        if op in ("&&", "||"):
            if a != "bool" or b != "bool":
                raise Untranslatable(f"{op} applied to a non-boolean")
            return "bool"
        if op in ("+", "-", "*"):
            if a != "long" or b != "long":
                raise Untranslatable(f"arithmetic on {a}/{b}, only int64 is supported")
            return "long"
        if op in ("==", "!="):
            if "null" not in (a, b) and a != b:
                raise Untranslatable(f"{op} compares {a} with {b}")
            return "bool"
        if op in ("<", "<=", ">", ">="):
            if a != b or a not in ("long", "temporal"):
                raise Untranslatable(f"{op} compares {a} with {b}")
            return "bool"
    raise Untranslatable(f"cannot type {n.kind}")


def referenced_fields(n: Node, acc: set | None = None) -> set:
    acc = set() if acc is None else acc
    if n.kind == "field":
        acc.add(n.text)
    for c in n.children:
        referenced_fields(c, acc)
    return acc


# -------------------------------------------------------------- SQL emitter

def sql_lit(n: Node) -> str:
    if n.lit_type == "string":
        return "'" + n.text.replace("'", "''") + "'"
    if n.lit_type == "bool":
        return n.text.upper()
    if n.lit_type == "null":
        return "NULL"
    return n.text


def to_sql(n: Node, fields: dict) -> str:
    if n.kind == "lit":
        return sql_lit(n)
    if n.kind == "field":
        return fields[n.text]["column"]
    if n.kind == "not":
        return f"NOT ({to_sql(n.children[0], fields)})"
    if n.kind == "impl":
        return (f"(NOT ({to_sql(n.children[0], fields)}) "
                f"OR ({to_sql(n.children[1], fields)}))")
    if n.kind == "call":
        col = fields[n.children[0].text]["column"]
        return f"({col} IS NOT NULL)" if n.text in PRESENCE_CALLS else f"({col} IS NULL)"
    if n.kind == "in":
        items = ", ".join(sql_lit(c) for c in n.children[1:])
        return f"({to_sql(n.children[0], fields)} IN ({items}))"
    if n.kind == "bin":
        op = {"==": "=", "!=": "<>", "&&": "AND", "||": "OR"}.get(n.text, n.text)
        a, b = (to_sql(c, fields) for c in n.children)
        if n.text in ("==", "!=") and any(
                c.kind == "lit" and c.lit_type == "null" for c in n.children):
            col = a if b == "NULL" else b
            return f"({col} IS {'NULL' if n.text == '==' else 'NOT NULL'})"
        return f"({a} {op} {b})"
    raise Untranslatable(f"no SQL for {n.kind}")


# ------------------------------------------------------------- Java emitter

def java_lit(n: Node, want: str) -> str:
    if n.lit_type == "string":
        return '"' + n.text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if n.lit_type == "bool":
        return n.text
    if n.lit_type == "null":
        return "null"
    return n.text + ("L" if want == "long" else "")


def to_java(n: Node, fields: dict) -> str:
    """Emit a Java boolean/long expression over local variables named after the
    fields.  The generated method declares those locals, so every numeric
    reference is already a primitive long and `==` is a value comparison."""
    if n.kind == "lit":
        return java_lit(n, "long" if n.lit_type == "long" else "")
    if n.kind == "field":
        return "v_" + n.text
    if n.kind == "not":
        return f"!({to_java(n.children[0], fields)})"
    if n.kind == "impl":
        return (f"(!({to_java(n.children[0], fields)}) "
                f"|| ({to_java(n.children[1], fields)}))")
    if n.kind == "call":
        ref = "v_" + n.children[0].text + "_present"
        return ref if n.text in PRESENCE_CALLS else f"!{ref}"
    if n.kind == "in":
        left = to_java(n.children[0], fields)
        cls = node_class(n.children[0], fields)
        items = ", ".join(java_lit(c, cls) for c in n.children[1:])
        if cls == "string":
            return f"java.util.List.of({items}).contains({left})"
        return "(" + " || ".join(
            f"{left} == {java_lit(c, cls)}" for c in n.children[1:]) + ")"
    if n.kind == "bin":
        op = n.text
        a, b = (to_java(c, fields) for c in n.children)
        ca, cb = (node_class(c, fields) for c in n.children)
        if op in ("==", "!="):
            if "null" in (ca, cb):
                nn = a if cb == "null" else b
                base = f"{nn} == null"
                return base if op == "==" else f"!({base})"
            if ca == "long":
                return f"({a} {op} {b})"
            eq = f"java.util.Objects.equals({a}, {b})"
            return eq if op == "==" else f"!{eq}"
        if op in ("<", "<=", ">", ">="):
            if ca == "temporal":
                return f"({a}.compareTo({b}) {op} 0)"
            return f"({a} {op} {b})"
        return f"({a} {op} {b})"
    raise Untranslatable(f"no Java for {n.kind}")


# ------------------------------------------------------------------- the API

@dataclass
class Translation:
    rule_id: str
    translated: bool
    reason: str = ""
    sql: str = ""
    java: str = ""
    fields: tuple = ()
    presence_fields: tuple = ()


def translate(rule: dict, fields: list[dict]) -> Translation:
    """fields = the control record's normalised fields[] list."""
    by_name = {f["name"]: f for f in fields}
    rid = rule["id"]
    try:
        node = Parser(tokenise(rule["assert"])).parse()
        if node_class(node, by_name) != "bool":
            raise Untranslatable("the expression is not a boolean assertion")
        used = sorted(referenced_fields(node))
        if not used:
            raise Untranslatable("the expression reads no control-record field")
        presence = sorted({n.children[0].text for n in _walk(node)
                           if n.kind == "call"})
        return Translation(rid, True,
                           sql=to_sql(node, by_name),
                           java=to_java(node, by_name),
                           fields=tuple(used),
                           presence_fields=tuple(presence))
    except Untranslatable as exc:
        return Translation(rid, False, reason=str(exc))
    except RecursionError:
        return Translation(rid, False, reason="expression nests too deeply")


def _walk(n: Node):
    yield n
    for c in n.children:
        yield from _walk(c)


# ------------------------------------------------------------- self-check
# Runs on `python3 rules_lang.py`.  This module is the one piece of new
# non-trivial logic in the generator, so it carries its own vectors.

def _selfcheck() -> int:
    F = [
        {"name": "balanceMinor", "type": "money", "column": "balance_minor"},
        {"name": "contributedCapitalMinor", "type": "money", "column": "contributed_capital_minor"},
        {"name": "capitalAtRisk", "type": "bool", "column": "capital_at_risk"},
        {"name": "fundsConfirmationSupported", "type": "bool", "column": "funds_confirmation_supported"},
        {"name": "status", "type": "enum", "column": "status"},
        {"name": "maturityDate", "type": "date", "column": "maturity_date"},
        {"name": "valueDate", "type": "date", "column": "value_date"},
        {"name": "providerRef", "type": "ref", "column": "provider_ref"},
        {"name": "psr", "type": "ratio", "column": "psr"},
    ]
    cases = [
        ("balanceMinor >= 0", True, "(balance_minor >= 0)", "(v_balanceMinor >= 0L)"),
        ("fundsConfirmationSupported == false && capitalAtRisk == true", True,
         "((funds_confirmation_supported = FALSE) AND (capital_at_risk = TRUE))",
         "(java.util.Objects.equals(v_fundsConfirmationSupported, false) && "
         "java.util.Objects.equals(v_capitalAtRisk, true))"),
        ("fundsConfirmationSupported == !capitalAtRisk", True, None, None),
        ("balanceMinor == contributedCapitalMinor - 5", True,
         "(balance_minor = (contributed_capital_minor - 5))",
         "(v_balanceMinor == (v_contributedCapitalMinor - 5L))"),
        ("maturityDate > valueDate", True, "(maturity_date > value_date)",
         "(v_maturityDate.compareTo(v_valueDate) > 0)"),
        ("status in ['ACTIVE','SUSPENDED']", True,
         "(status IN ('ACTIVE', 'SUSPENDED'))", None),
        ("status == 'ACTIVE' -> present(providerRef)", True,
         "(NOT ((status = 'ACTIVE')) OR ((provider_ref IS NOT NULL)))", None),
        ("absent(providerRef)", True, "(provider_ref IS NULL)", "!v_providerRef_present"),
        ("implies(capitalAtRisk == true, fundsConfirmationSupported == false)", True,
         "(NOT ((capital_at_risk = TRUE)) OR ((funds_confirmation_supported = FALSE)))", None),
        ("not(capitalAtRisk)", True, "NOT (capital_at_risk)", "!(v_capitalAtRisk)"),
        ("cr.status == 'ACTIVE' implies cr.providerRef is not null", True,
         "(NOT ((status = 'ACTIVE')) OR ((provider_ref IS NOT NULL)))", None),
        ("status not in ['CLOSED']", True, "NOT ((status IN ('CLOSED')))", None),
        ("providerRef is null", True, "(provider_ref IS NULL)", None),
        ("bq.psr.share == 1", False, None, None),
        ("BoardCompositionPolicy.max is not null", False, None, None),
        # outside the grammar — must be refused, not approximated
        ("count(bq.psr where effectiveFrom <= x) == 1", False, None, None),
        ("sum(legs.amountMinor) == balanceMinor", False, None, None),
        ("psr == 1", False, None, None),
        ("unknownField >= 0", False, None, None),
        ("immutable(status)", False, None, None),
        ("balanceMinor", False, None, None),
        ("status == 1", False, None, None),
    ]
    failures = []
    for expr, want_ok, want_sql, want_java in cases:
        t = translate({"id": "T", "assert": expr}, F)
        if t.translated != want_ok:
            failures.append(f"{expr!r}: translated={t.translated} want {want_ok} "
                            f"({t.reason})")
            continue
        if want_sql and t.sql != want_sql:
            failures.append(f"{expr!r}: SQL\n  got  {t.sql}\n  want {want_sql}")
        if want_java and t.java != want_java:
            failures.append(f"{expr!r}: Java\n  got  {t.java}\n  want {want_java}")
    for f in failures:
        print("FAIL", f)
    print(f"rules_lang self-check: {len(cases) - len(failures)}/{len(cases)} cases pass")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_selfcheck())
