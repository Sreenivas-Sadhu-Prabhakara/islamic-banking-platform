package com.bank.platform.controlrecord.money;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class Iso4217Test {

    @Test
    void the_three_decimal_gulf_currencies_are_not_two_decimal() {
        // A hardcoded x100 is a bug, and these are the currencies an Islamic
        // banking estate meets first.
        assertThat(Iso4217.exponent("BHD")).isEqualTo(3);
        assertThat(Iso4217.exponent("KWD")).isEqualTo(3);
        assertThat(Iso4217.exponent("OMR")).isEqualTo(3);
        assertThat(Iso4217.exponent("TND")).isEqualTo(3);
        assertThat(Iso4217.exponent("JOD")).isEqualTo(3);
    }

    @Test
    void zero_and_four_decimal_currencies() {
        assertThat(Iso4217.exponent("JPY")).isZero();
        assertThat(Iso4217.exponent("XOF")).isZero();
        assertThat(Iso4217.exponent("CLF")).isEqualTo(4);
    }

    @Test
    void unlisted_currencies_default_to_two() {
        assertThat(Iso4217.exponent("USD")).isEqualTo(2);
        assertThat(Iso4217.exponent("MYR")).isEqualTo(2);
    }

    @Test
    void a_malformed_code_throws_rather_than_assuming_two() {
        assertThatThrownBy(() -> Iso4217.exponent("usd")).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> Iso4217.exponent(null)).isInstanceOf(IllegalArgumentException.class);
        assertThat(Iso4217.isWellFormed("US")).isFalse();
    }
}
