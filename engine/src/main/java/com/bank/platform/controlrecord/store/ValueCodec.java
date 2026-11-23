package com.bank.platform.controlrecord.store;

import com.bank.platform.controlrecord.spec.Field;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Wire value &lt;-&gt; column value, per field type.
 *
 * The two composite types are the whole reason this exists: a {@code ratio}
 * occupies {@code <col>_numerator} and {@code <col>_denominator}, and a
 * {@code period} occupies {@code <col>_from} and {@code <col>_to}. One field
 * is not one column, and a codec that assumed it was would silently drop the
 * denominator of every profit-sharing ratio in the estate.
 */
public final class ValueCodec {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private ValueCodec() { }

    /** The column values for one field, in the same order as {@link Field#columns()}. */
    public static List<Object> toColumns(Field field, Object value) {
        List<Object> out = new ArrayList<>();
        switch (field.type()) {
            case RATIO -> {
                Map<?, ?> m = value instanceof Map<?, ?> r ? r : Map.of();
                out.add(asLong(m.get("numerator")));
                out.add(asLong(m.get("denominator")));
            }
            case PERIOD -> {
                Map<?, ?> m = value instanceof Map<?, ?> p ? p : Map.of();
                out.add(asDate(m.get("from")));
                out.add(asDate(m.get("to")));
            }
            case MONEY, INT64 -> out.add(asLong(value));
            case INT32 -> out.add(value == null ? null : ((Number) value).intValue());
            case DATE -> out.add(asDate(value));
            case TIMESTAMP -> out.add(value == null ? null : OffsetDateTime.parse(String.valueOf(value)));
            case ARRAY -> out.add(json(value));
            default -> out.add(value);
        }
        return out;
    }

    /** Rebuilds one field's wire value from the row, reassembling composites. */
    public static Object fromColumns(Field field, Map<String, Object> row) {
        List<String> cols = field.columns().stream()
                .map(com.bank.platform.controlrecord.spec.FieldType.Column::name).toList();
        switch (field.type()) {
            case RATIO -> {
                Object n = row.get(cols.get(0));
                Object d = row.get(cols.get(1));
                if (n == null && d == null) {
                    return null;
                }
                return new LinkedHashMap<>(Map.of("numerator", asLong(n), "denominator", asLong(d)));
            }
            case PERIOD -> {
                Object from = row.get(cols.get(0));
                Object to = row.get(cols.get(1));
                if (from == null && to == null) {
                    return null;
                }
                Map<String, Object> period = new LinkedHashMap<>();
                period.put("from", from == null ? null : String.valueOf(from));
                period.put("to", to == null ? null : String.valueOf(to));
                return period;
            }
            case ARRAY -> {
                Object raw = row.get(cols.get(0));
                return raw == null ? null : unjson(String.valueOf(raw));
            }
            case DATE, TIMESTAMP -> {
                Object raw = row.get(cols.get(0));
                return raw == null ? null : String.valueOf(raw);
            }
            default -> {
                return row.get(cols.get(0));
            }
        }
    }

    private static Long asLong(Object value) {
        return value == null ? null : ((Number) value).longValue();
    }

    private static LocalDate asDate(Object value) {
        return value == null ? null : LocalDate.parse(String.valueOf(value));
    }

    private static String json(Object value) {
        try {
            return value == null ? null : MAPPER.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("array field is not serialisable", e);
        }
    }

    private static Object unjson(String raw) {
        try {
            return MAPPER.readValue(raw, List.class);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("stored array column is not JSON: " + raw, e);
        }
    }
}
