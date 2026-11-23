package com.bank.platform.controlrecord.money;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class RatioTest {

    @Test
    void a_third_plus_two_thirds_is_exactly_one() {
        // The reason a ratio is not a double: 1.0/3 + 2.0/3 != 1.0 in binary
        // floating point, and a profit-sharing ratio that fails to total one
        // is a different contract.
        assertThat(Ratio.of(1, 3).plus(Ratio.of(2, 3)).isOne()).isTrue();
        assertThat(Ratio.of(1, 3).plus(Ratio.of(2, 3))).isEqualTo(Ratio.ONE);
    }

    @Test
    void addition_reduces() {
        assertThat(Ratio.of(1, 4).plus(Ratio.of(1, 4))).isEqualTo(Ratio.of(1, 2));
    }

    @Test
    void comparison_is_by_cross_multiplication() {
        assertThat(Ratio.of(2, 5).lte(Ratio.of(3, 5))).isTrue();
        assertThat(Ratio.of(3, 5).lte(Ratio.of(2, 5))).isFalse();
        assertThat(Ratio.of(1, 3).lte(Ratio.of(2, 6))).isTrue();
    }

    @Test
    void a_non_positive_denominator_is_refused() {
        assertThatThrownBy(() -> Ratio.of(1, 0)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> Ratio.of(1, -3)).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void overflow_throws_instead_of_wrapping_to_a_wrong_share() {
        assertThatThrownBy(() -> Ratio.of(Long.MAX_VALUE, 3).plus(Ratio.of(1, 2)))
                .isInstanceOf(ArithmeticException.class);
        assertThatThrownBy(() -> Ratio.of(Long.MAX_VALUE, 1).lte(Ratio.of(1, 7)))
                .isInstanceOf(ArithmeticException.class);
    }
}
