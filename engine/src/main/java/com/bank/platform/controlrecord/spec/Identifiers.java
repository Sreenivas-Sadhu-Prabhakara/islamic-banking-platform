package com.bank.platform.controlrecord.spec;

import java.util.regex.Pattern;

/**
 * The SQL-identifier gate.
 *
 * Every value the engine writes is a bind parameter, but a table or column
 * name cannot be one — it is concatenated into the statement. So identifiers
 * are checked once, here, when the spec is loaded, and a spec that fails to
 * load cannot serve traffic. The catalog schema already constrains these with
 * the same pattern; this enforces it at the boundary rather than trusting that
 * the file on disk is the file the schema validated.
 */
public final class Identifiers {

    public static final Pattern SAFE = Pattern.compile("^[a-z][a-z0-9_]{0,62}$");

    private Identifiers() { }

    public static String require(String identifier, String what) {
        if (identifier == null || !SAFE.matcher(identifier).matches()) {
            throw new IllegalArgumentException(
                    what + " is not a safe SQL identifier: " + identifier);
        }
        return identifier;
    }
}
