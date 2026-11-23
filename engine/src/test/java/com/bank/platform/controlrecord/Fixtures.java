package com.bank.platform.controlrecord;

import com.bank.platform.controlrecord.spec.BehaviourQualifierSpec;
import com.bank.platform.controlrecord.spec.ControlRecordSpec;
import com.bank.platform.controlrecord.spec.DomainSpec;
import com.bank.platform.controlrecord.spec.Field;
import com.bank.platform.controlrecord.spec.FieldType;

import java.util.List;

/** A spec shaped like the real Mudarabah Savings Account entry, kept small. */
public final class Fixtures {

    private Fixtures() { }

    public static Field field(String name, FieldType type, boolean required) {
        return new Field(name, snake(name), type, required, List.of(),
                null, null, false, null, null, null, null);
    }

    public static Field enumField(String name, boolean required, List<String> values) {
        return new Field(name, snake(name), FieldType.ENUM, required, values,
                null, null, false, null, null, null, null);
    }

    public static Field constEnum(String name, String only) {
        return new Field(name, snake(name), FieldType.ENUM, true, List.of(only),
                only, null, false, null, null, null, null);
    }

    public static Field money(String name, boolean nonNegative, String currencyField) {
        return new Field(name, snake(name), FieldType.MONEY, true, List.of(),
                null, currencyField, nonNegative, null, null, null, null);
    }

    public static Field ratio(String name, long maxDenominator) {
        return new Field(name, snake(name), FieldType.RATIO, true, List.of(),
                null, null, false, maxDenominator, null, null, null);
    }

    public static ControlRecordSpec controlRecord() {
        return new ControlRecordSpec(
                "Mudarabah Savings Account Fulfillment Arrangement",
                "mudarabah_savings_account",
                "accountId",
                List.of(
                        field("accountId", FieldType.ID, true),
                        field("customerReference", FieldType.REF, true),
                        field("currency", FieldType.CURRENCY, true),
                        enumField("status", true,
                                List.of("INITIATED", "PENDING_KYC", "ACTIVE", "SUSPENDED", "TERMINATED")),
                        constEnum("contractType", "Mudarabah"),
                        money("balanceMinor", true, null),
                        ratio("psrIahShare", 1_000_000L),
                        field("openedOn", FieldType.DATE, false)));
    }

    public static DomainSpec domain() {
        return new DomainSpec("Mudarabah Savings Account", "mudarabah-savings-account",
                "Fulfill", "Mudarabah Savings Account Facility",
                "Deposits and Investment Accounts", "Islamic Deposits",
                controlRecord().name(), controlRecord(),
                List.of(new BehaviourQualifierSpec("Profit Sharing Agreement",
                        "profit-sharing-agreement", "profit_sharing_agreement",
                        List.of(field("agreementId", FieldType.ID, true),
                                ratio("psrMudaribShare", 1_000_000L)))));
    }

    private static String snake(String camel) {
        return camel.replaceAll("([a-z0-9])([A-Z])", "$1_$2").toLowerCase();
    }
}
