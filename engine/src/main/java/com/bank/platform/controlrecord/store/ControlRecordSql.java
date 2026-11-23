package com.bank.platform.controlrecord.store;

import com.bank.platform.controlrecord.spec.BehaviourQualifierSpec;
import com.bank.platform.controlrecord.spec.ControlRecordSpec;
import com.bank.platform.controlrecord.spec.FieldType;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Builds the engine's statements from a spec.
 *
 * Two rules hold for every statement here, and they are the reason this is a
 * separate class with its own tests rather than strings inline in the store:
 *
 * 1. Every VALUE is a bind parameter. There is no string interpolation of
 *    anything a caller can influence.
 * 2. Every statement filters on {@code tenant_id}. There is no overload
 *    without it, so a tenantless query cannot be written by accident — which
 *    is how the generated repository it replaces ended up with none at all
 *    across 11 tables.
 *
 * Identifiers are concatenated because SQL cannot bind them; they are checked
 * against {@link com.bank.platform.controlrecord.spec.Identifiers} when the
 * spec loads, so a spec that could inject cannot be served.
 */
public final class ControlRecordSql {

    public static final String TENANT_COLUMN = "tenant_id";

    private ControlRecordSql() { }

    public static String insert(ControlRecordSpec spec) {
        List<String> cols = columnNames(spec);
        String placeholders = cols.stream().map(c -> "?").collect(Collectors.joining(", "));
        return "INSERT INTO " + spec.table() + " (" + TENANT_COLUMN + ", "
                + String.join(", ", cols) + ") VALUES (?, " + placeholders + ")";
    }

    public static String selectById(ControlRecordSpec spec) {
        return "SELECT " + String.join(", ", columnNames(spec)) + " FROM " + spec.table()
                + " WHERE " + TENANT_COLUMN + " = ? AND " + pkColumn(spec) + " = ?";
    }

    public static String selectAll(ControlRecordSpec spec) {
        return "SELECT " + String.join(", ", columnNames(spec)) + " FROM " + spec.table()
                + " WHERE " + TENANT_COLUMN + " = ? ORDER BY " + pkColumn(spec) + " LIMIT ?";
    }

    /** @param columns the columns actually being written, in order */
    public static String update(ControlRecordSpec spec, List<String> columns) {
        if (columns.isEmpty()) {
            throw new IllegalArgumentException("an update must write at least one column");
        }
        String assignments = columns.stream().map(c -> c + " = ?").collect(Collectors.joining(", "));
        return "UPDATE " + spec.table() + " SET " + assignments
                + " WHERE " + TENANT_COLUMN + " = ? AND " + pkColumn(spec) + " = ?";
    }

    /**
     * A behaviour qualifier's rows for one control record. The child table
     * carries the parent's primary-key column; there is no cross-service
     * foreign key, because each service domain owns its own schema.
     */
    public static String selectBehaviourQualifier(BehaviourQualifierSpec bq, ControlRecordSpec parent) {
        List<String> cols = bq.fields().stream()
                .flatMap(f -> f.columns().stream()).map(FieldType.Column::name).toList();
        return "SELECT " + String.join(", ", cols) + " FROM " + bq.table()
                + " WHERE " + TENANT_COLUMN + " = ? AND " + pkColumn(parent) + " = ?";
    }

    public static String pkColumn(ControlRecordSpec spec) {
        return spec.primaryKeyField().column();
    }

    static List<String> columnNames(ControlRecordSpec spec) {
        return spec.columns().stream().map(FieldType.Column::name).toList();
    }
}
