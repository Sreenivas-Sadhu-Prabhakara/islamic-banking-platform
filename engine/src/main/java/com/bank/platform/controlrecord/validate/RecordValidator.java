package com.bank.platform.controlrecord.validate;

import com.bank.platform.controlrecord.money.Iso4217;
import com.bank.platform.controlrecord.spec.ControlRecordSpec;
import com.bank.platform.controlrecord.spec.Field;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Validates a write against the catalog's field definitions.
 *
 * This class is the whole point of catalog schema v2. The scaffold it replaces
 * accepted {@code Map<String, Object> properties} with
 * {@code additionalProperties: true} — so every one of the 203 shallow service
 * domains would take any JSON at all, and a Mudarabah account would accept a
 * negative balance, an unknown status and a profit-sharing ratio of 1.5
 * without complaint. Nothing here is domain-specific: every rule below is read
 * out of the catalog entry.
 */
public final class RecordValidator {

    private final ControlRecordSpec spec;

    public RecordValidator(ControlRecordSpec spec) {
        this.spec = spec;
    }

    /**
     * @param partial true for an Update, where absent fields are "unchanged"
     *                rather than "missing"
     */
    public List<Violation> validate(Map<String, Object> body, boolean partial) {
        List<Violation> out = new ArrayList<>();

        for (String name : body.keySet()) {
            if (spec.field(name).isEmpty()) {
                out.add(Violation.of(name, "UNKNOWN_FIELD",
                        "not a field of " + spec.name() + "; this record declares "
                                + "additionalProperties:false"));
            }
        }

        for (Field f : spec.fields()) {
            Object value = body.get(f.name());
            if (value == null) {
                if (f.required() && !partial) {
                    out.add(Violation.of(f.name(), "REQUIRED", "required field is absent"));
                }
                continue;
            }
            checkField(f, value, body, partial, out);
        }
        return out;
    }

    private void checkField(Field f, Object value, Map<String, Object> body, boolean partial,
                            List<Violation> out) {
        switch (f.type()) {
            case ID, REF, STRING -> {
                String s = string(f, value, out);
                if (s != null && f.maxLength() != null && s.length() > f.maxLength()) {
                    out.add(Violation.of(f.name(), "TOO_LONG",
                            "longer than maxLength " + f.maxLength()));
                }
            }
            case ENUM -> {
                String s = string(f, value, out);
                if (s != null && !f.permitted().isEmpty() && !f.permitted().contains(s)) {
                    out.add(Violation.of(f.name(), "NOT_PERMITTED",
                            "'" + s + "' is not one of " + f.permitted()));
                }
            }
            case BOOL -> {
                if (!(value instanceof Boolean b)) {
                    out.add(Violation.of(f.name(), "NOT_BOOLEAN", "expected a boolean"));
                } else if (f.constValue() != null && !f.constValue().equals(b)) {
                    out.add(Violation.of(f.name(), "NOT_PERMITTED",
                            "this field may only be " + f.constValue()));
                }
            }
            case INT32, INT64 -> {
                Long n = integral(f, value, out);
                if (n != null) {
                    if (f.min() != null && n < f.min()) {
                        out.add(Violation.of(f.name(), "BELOW_MIN", "below min " + f.min()));
                    }
                    if (f.max() != null && n > f.max()) {
                        out.add(Violation.of(f.name(), "ABOVE_MAX", "above max " + f.max()));
                    }
                }
            }
            case MONEY -> {
                Long minor = integral(f, value, out);
                if (minor == null) {
                    return;
                }
                if (f.nonNegative() && minor < 0) {
                    out.add(Violation.of(f.name(), "NEGATIVE", "this amount may not be negative"));
                }
                // An amount in MINOR units is meaningless without its currency:
                // the exponent decides what the integer means.
                String currencyName = f.currencyField() != null ? f.currencyField() : soleCurrencyField();
                if (currencyName == null) {
                    out.add(Violation.of(f.name(), "NO_CURRENCY",
                            "minor units cannot be scaled: the record names no currency field "
                                    + "for this amount"));
                    return;
                }
                Object code = body.get(currencyName);
                if (code == null) {
                    // On an Update the stored currency stands: this amount's
                    // scale is fixed by the record, not by this request, so
                    // demanding the code again would force every client to
                    // resend it with every balance patch.
                    if (!partial) {
                        out.add(Violation.of(f.name(), "NO_CURRENCY",
                                "'" + currencyName + "' carries this amount's ISO 4217 code and is absent"));
                    }
                } else if (!Iso4217.isWellFormed(String.valueOf(code))) {
                    out.add(Violation.of(currencyName, "NOT_ISO4217",
                            "not an ISO 4217 alpha-3 code: " + code));
                }
            }
            case CURRENCY -> {
                String s = string(f, value, out);
                if (s != null && !Iso4217.isWellFormed(s)) {
                    out.add(Violation.of(f.name(), "NOT_ISO4217",
                            "not an ISO 4217 alpha-3 code: " + s));
                }
            }
            case COUNTRY_CODE -> {
                String s = string(f, value, out);
                if (s != null && !s.matches("^[A-Z]{2}$")) {
                    out.add(Violation.of(f.name(), "NOT_ISO3166",
                            "not an ISO 3166-1 alpha-2 code: " + s));
                }
            }
            case DATE -> {
                String s = string(f, value, out);
                if (s != null) {
                    parseDate(f.name(), s, out);
                }
            }
            case TIMESTAMP -> {
                String s = string(f, value, out);
                if (s != null) {
                    try {
                        OffsetDateTime.parse(s);
                    } catch (DateTimeParseException e) {
                        out.add(Violation.of(f.name(), "NOT_TIMESTAMP",
                                "not an RFC 3339 date-time: " + s));
                    }
                }
            }
            case RATIO -> checkRatio(f, value, out);
            case PERIOD -> checkPeriod(f, value, out);
            case ARRAY -> {
                if (!(value instanceof List<?>)) {
                    out.add(Violation.of(f.name(), "NOT_ARRAY", "expected an array"));
                }
            }
            default -> throw new IllegalStateException("unhandled field type " + f.type());
        }
    }

    private void checkRatio(Field f, Object value, List<Violation> out) {
        if (!(value instanceof Map<?, ?> m)) {
            out.add(Violation.of(f.name(), "NOT_RATIO",
                    "expected {numerator, denominator} — a ratio is an exact int64 pair, not a decimal"));
            return;
        }
        Long n = integral(f, m.get("numerator"), out);
        Long d = integral(f, m.get("denominator"), out);
        if (n == null || d == null) {
            return;
        }
        if (d <= 0) {
            out.add(Violation.of(f.name(), "BAD_DENOMINATOR", "denominator must be positive"));
            return;
        }
        if (f.maxDenominator() != null && d > f.maxDenominator()) {
            out.add(Violation.of(f.name(), "DENOMINATOR_TOO_LARGE",
                    "denominator " + d + " exceeds maxDenominator " + f.maxDenominator()
                            + ", beyond which cross-multiplying two ratios can overflow int64"));
        }
    }

    private void checkPeriod(Field f, Object value, List<Violation> out) {
        if (!(value instanceof Map<?, ?> m)) {
            out.add(Violation.of(f.name(), "NOT_PERIOD", "expected {from, to}"));
            return;
        }
        LocalDate from = m.get("from") == null ? null : parseDate(f.name(), String.valueOf(m.get("from")), out);
        LocalDate to = m.get("to") == null ? null : parseDate(f.name(), String.valueOf(m.get("to")), out);
        if (from != null && to != null && from.isAfter(to)) {
            out.add(Violation.of(f.name(), "PERIOD_REVERSED", "from is after to"));
        }
    }

    private LocalDate parseDate(String field, String value, List<Violation> out) {
        try {
            return LocalDate.parse(value);
        } catch (DateTimeParseException e) {
            out.add(Violation.of(field, "NOT_DATE", "not an ISO-8601 date: " + value));
            return null;
        }
    }

    private String string(Field f, Object value, List<Violation> out) {
        if (value instanceof String s) {
            return s;
        }
        out.add(Violation.of(f.name(), "NOT_STRING", "expected a string"));
        return null;
    }

    private Long integral(Field f, Object value, List<Violation> out) {
        if (value instanceof Integer i) {
            return i.longValue();
        }
        if (value instanceof Long l) {
            return l;
        }
        if (value instanceof java.math.BigInteger b) {
            return b.longValueExact();
        }
        out.add(Violation.of(f.name(), "NOT_INTEGER",
                "expected an integer; this estate has no decimal type on the wire"));
        return null;
    }

    /** The record's single currency field, when a money field names none explicitly. */
    private String soleCurrencyField() {
        List<Field> currencies = spec.fields().stream()
                .filter(f -> f.type() == com.bank.platform.controlrecord.spec.FieldType.CURRENCY)
                .toList();
        return currencies.size() == 1 ? currencies.get(0).name() : null;
    }
}
