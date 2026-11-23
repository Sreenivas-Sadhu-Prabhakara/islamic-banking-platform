package com.bank.platform.controlrecord.spec;

import java.util.List;

/**
 * A BIAN behaviour qualifier: a read-only sub-resource plus its own child
 * table, keyed by the parent control record's primary key.
 *
 * A qualifier the catalog named but gave no fields is NOT one of these — the
 * generator emits no table and no path for it and reports it as a gap, so a
 * documented intent never becomes a half-built endpoint.
 */
public record BehaviourQualifierSpec(String name, String path, String table, List<Field> fields) {

    public BehaviourQualifierSpec {
        Identifiers.require(table, "behaviourQualifier.table");
        if (!path.matches("^[a-z0-9][a-z0-9-]*$")) {
            throw new IllegalArgumentException("behaviourQualifier.path is not a URL segment: " + path);
        }
        fields = List.copyOf(fields);
    }
}
