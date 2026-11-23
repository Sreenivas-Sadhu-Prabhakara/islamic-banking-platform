package com.bank.platform.controlrecord.spec;

import java.util.List;

/**
 * One catalog field: one OpenAPI property, one Java accessor and one or two
 * columns. Everything the engine does with a field is derived from here.
 *
 * @param name          camelCase wire name
 * @param column        snake_case base column name
 * @param type          the closed-vocabulary type
 * @param required      whether a write must carry it
 * @param values        permitted values; non-empty only for {@link FieldType#ENUM}
 * @param constValue    the single permitted value, or null
 * @param currencyField name of the field carrying this amount's ISO 4217 code
 * @param nonNegative   money only: the amount may not be negative
 * @param maxDenominator ratio only: the largest denominator that keeps
 *                       cross-multiplication inside int64
 */
public record Field(
        String name,
        String column,
        FieldType type,
        boolean required,
        List<String> values,
        Object constValue,
        String currencyField,
        boolean nonNegative,
        Long maxDenominator,
        Integer min,
        Integer max,
        Integer maxLength) {

    public Field {
        values = values == null ? List.of() : List.copyOf(values);
    }

    public List<FieldType.Column> columns() {
        return type.columns(column);
    }

    /** The values a write may carry: the const alone if there is one, else the enum. */
    public List<String> permitted() {
        return constValue == null ? values : List.of(String.valueOf(constValue));
    }
}
