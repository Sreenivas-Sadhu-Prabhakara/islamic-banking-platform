package com.bank.platform.controlrecord.money;

import java.util.Map;

/**
 * The ONE ISO 4217 minor-unit exponent table for the whole estate.
 *
 * Money crosses this estate as a signed int64 count of MINOR units, so a
 * hardcoded x100 is a bug: BHD, IQD, JOD, KWD, LYD, OMR and TND are
 * 3-decimal — the Islamic markets' own currencies are the first to break a
 * 2-decimal assumption — JPY, KRW and the CFA francs are 0-decimal, and
 * CLF and UYW are 4-decimal.
 *
 * It used to be generated into every service, one copy each. A table that is
 * copied is a table that drifts.
 */
public final class Iso4217 {

    private static final Map<String, Integer> EXPONENTS = Map.ofEntries(
            Map.entry("BHD", 3), Map.entry("IQD", 3), Map.entry("JOD", 3),
            Map.entry("KWD", 3), Map.entry("LYD", 3), Map.entry("OMR", 3),
            Map.entry("TND", 3),
            Map.entry("BIF", 0), Map.entry("CLP", 0), Map.entry("DJF", 0),
            Map.entry("GNF", 0), Map.entry("ISK", 0), Map.entry("JPY", 0),
            Map.entry("KMF", 0), Map.entry("KRW", 0), Map.entry("PYG", 0),
            Map.entry("RWF", 0), Map.entry("UGX", 0), Map.entry("UYI", 0),
            Map.entry("VND", 0), Map.entry("VUV", 0), Map.entry("XAF", 0),
            Map.entry("XOF", 0), Map.entry("XPF", 0),
            Map.entry("CLF", 4), Map.entry("UYW", 4));

    private Iso4217() { }

    /** True for a syntactically valid alpha-3 code. Membership is not claimed. */
    public static boolean isWellFormed(String currency) {
        return currency != null && currency.matches("^[A-Z]{3}$");
    }

    /** @return the minor-unit exponent; 2 for every currency not listed. */
    public static int exponent(String currency) {
        if (!isWellFormed(currency)) {
            throw new IllegalArgumentException(
                    "an ISO 4217 alpha-3 code is required to scale minor units, got: " + currency);
        }
        return EXPONENTS.getOrDefault(currency, 2);
    }
}
