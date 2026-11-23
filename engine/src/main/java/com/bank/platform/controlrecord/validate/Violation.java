package com.bank.platform.controlrecord.validate;

/**
 * One rejected field. {@code code} is stable and machine-readable; the message
 * says which rule of the catalog it broke.
 */
public record Violation(String field, String code, String message) {

    public static Violation of(String field, String code, String message) {
        return new Violation(field, code, message);
    }
}
