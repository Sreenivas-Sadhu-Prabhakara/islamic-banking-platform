package com.bank.platform.controlrecord.money;

/**
 * An exact rational, as two int64s. A profit-sharing ratio is never a float:
 * 1/3 to an Islamic investment account is a contractual share, and a binary
 * floating-point approximation of it is a different contract.
 *
 * Comparison and addition are by cross-multiplication under
 * {@link Math#multiplyExact}, so an overflow throws instead of wrapping to a
 * wrong answer. The catalog's {@code maxDenominator} exists to keep legitimate
 * values far away from that edge.
 */
public record Ratio(long numerator, long denominator) {

    public Ratio {
        if (denominator <= 0) {
            throw new IllegalArgumentException("denominator must be positive, got " + denominator);
        }
    }

    public static Ratio of(long numerator, long denominator) {
        return new Ratio(numerator, denominator);
    }

    public static final Ratio ONE = new Ratio(1, 1);

    public Ratio plus(Ratio other) {
        long n = Math.addExact(
                Math.multiplyExact(numerator, other.denominator),
                Math.multiplyExact(other.numerator, denominator));
        return new Ratio(n, Math.multiplyExact(denominator, other.denominator)).reduced();
    }

    public boolean lte(Ratio other) {
        return Math.multiplyExact(numerator, other.denominator)
                <= Math.multiplyExact(other.numerator, denominator);
    }

    public boolean isOne() {
        return numerator == denominator;
    }

    public Ratio reduced() {
        long g = gcd(Math.abs(numerator), denominator);
        return g <= 1 ? this : new Ratio(numerator / g, denominator / g);
    }

    private static long gcd(long a, long b) {
        while (b != 0) {
            long t = a % b;
            a = b;
            b = t;
        }
        return a == 0 ? 1 : a;
    }
}
