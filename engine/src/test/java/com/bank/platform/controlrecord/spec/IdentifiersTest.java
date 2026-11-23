package com.bank.platform.controlrecord.spec;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class IdentifiersTest {

    @Test
    void accepts_a_snake_case_identifier() {
        assertThat(Identifiers.require("mudarabah_savings_account", "table"))
                .isEqualTo("mudarabah_savings_account");
    }

    @Test
    void rejects_anything_that_could_leave_the_identifier_position() {
        List<String> attacks = List.of(
                "t; DROP TABLE accounts",
                "t\" UNION SELECT",
                "t--",
                "t ",
                "T_UPPER",
                "1_leading_digit",
                "");
        assertThat(attacks).allSatisfy(bad ->
                assertThatThrownBy(() -> Identifiers.require(bad, "table"))
                        .isInstanceOf(IllegalArgumentException.class)
                        .hasMessageContaining("not a safe SQL identifier"));
    }

    @Test
    void a_spec_with_an_unsafe_table_name_cannot_be_constructed() {
        assertThatThrownBy(() -> new ControlRecordSpec("X", "t; DROP TABLE x", "id",
                List.of(new Field("id", "id", FieldType.ID, true, List.of(),
                        null, null, false, null, null, null, null))))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
