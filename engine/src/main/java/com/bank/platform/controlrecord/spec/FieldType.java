package com.bank.platform.controlrecord.spec;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * The closed type vocabulary of catalog schema v2 — in ONE place.
 *
 * Before this enum the same 15 types were spelled out three times in the
 * generator ({@code SQL_TYPE}, {@code JAVA_TYPE} and {@code _columns}), and
 * {@code SQL_TYPE} was already missing {@code ratio} and {@code period}
 * because those are the two that expand to more than one column. A type whose
 * SQL shape and whose column count are decided in different tables is a type
 * that will eventually disagree with itself.
 *
 * There is deliberately no {@code decimal}, no {@code float} and no
 * {@code number}: money is a signed int64 count of MINOR units and a ratio is
 * an exact int64 pair.
 */
public enum FieldType {

    ID("id", "VARCHAR(64)"),
    REF("ref", "VARCHAR(64)"),
    STRING("string", "TEXT"),
    ENUM("enum", "TEXT"),
    BOOL("bool", "BOOLEAN"),
    INT32("int32", "INTEGER"),
    INT64("int64", "BIGINT"),
    MONEY("money", "BIGINT"),
    CURRENCY("currency", "CHAR(3)"),
    COUNTRY_CODE("countryCode", "CHAR(2)"),
    DATE("date", "DATE"),
    TIMESTAMP("timestamp", "TIMESTAMP WITH TIME ZONE"),
    ARRAY("array", "TEXT"),

    /** Exact rational: two BIGINT columns, never one floating-point column. */
    RATIO("ratio", "BIGINT", "_numerator", "_denominator"),
    /** Closed date range: two DATE columns. */
    PERIOD("period", "DATE", "_from", "_to");

    /** One physical column of a field. */
    public record Column(String name, String sqlType) { }

    private static final Map<String, FieldType> BY_WORD = Stream.of(values())
            .collect(Collectors.toUnmodifiableMap(FieldType::word, Function.identity()));

    private final String word;
    private final String sqlType;
    private final List<String> suffixes;

    FieldType(String word, String sqlType, String... suffixes) {
        this.word = word;
        this.sqlType = sqlType;
        this.suffixes = List.of(suffixes);
    }

    /** The catalog's own spelling of this type. */
    public String word() {
        return word;
    }

    /** True when one catalog field becomes more than one column. */
    public boolean composite() {
        return !suffixes.isEmpty();
    }

    /**
     * The column(s) one field of this type occupies.
     *
     * @param base the field's snake_case column name from the catalog
     */
    public List<Column> columns(String base) {
        if (suffixes.isEmpty()) {
            return List.of(new Column(base, sqlType));
        }
        return suffixes.stream().map(s -> new Column(base + s, sqlType)).toList();
    }

    /**
     * @throws IllegalArgumentException for any word outside the vocabulary —
     *         an unknown type is a malformed catalog, never a free-form string
     *         column. That silent fallback is what produced 203 identical
     *         services.
     */
    public static FieldType of(String word) {
        FieldType t = BY_WORD.get(word);
        if (t == null) {
            throw new IllegalArgumentException(
                    "unknown catalog field type '" + word + "'; the vocabulary is " + BY_WORD.keySet());
        }
        return t;
    }
}
