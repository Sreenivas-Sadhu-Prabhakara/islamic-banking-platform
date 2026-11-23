package com.bank.platform.controlrecord.spec;

import java.util.List;
import java.util.Optional;

/**
 * The one BIAN control record a service domain manages.
 *
 * @param table      Postgres table, already checked against
 *                   {@link Identifiers#SAFE} — this is the SQL-injection
 *                   boundary, because a table name cannot be a bind parameter
 * @param primaryKey the field that is the PRIMARY KEY
 */
public record ControlRecordSpec(String name, String table, String primaryKey, List<Field> fields) {

    public ControlRecordSpec {
        Identifiers.require(table, "controlRecord.table");
        fields = List.copyOf(fields);
    }

    public Optional<Field> field(String name) {
        return fields.stream().filter(f -> f.name().equals(name)).findFirst();
    }

    public Field primaryKeyField() {
        return field(primaryKey).orElseThrow(() -> new IllegalStateException(
                "primaryKey '" + primaryKey + "' is not a field of " + name));
    }

    /**
     * The enum field carrying the record's lifecycle status, if the domain has
     * one. The BIAN Control action term is offered only for the values this
     * field actually declares — the scaffold it replaces hardcoded
     * INITIATED/ACTIVE/SUSPENDED/TERMINATED for all 203 domains whether or not
     * the domain had such a lifecycle.
     */
    public Optional<Field> statusField() {
        return field("status").filter(f -> f.type() == FieldType.ENUM);
    }

    public List<FieldType.Column> columns() {
        return fields.stream().flatMap(f -> f.columns().stream()).toList();
    }
}
