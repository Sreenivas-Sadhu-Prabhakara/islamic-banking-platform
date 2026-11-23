package com.bank.platform.controlrecord.spec;

import java.util.List;
import java.util.Optional;

/**
 * One service domain, as data. This is the whole input the engine needs to
 * serve a domain: there is no per-domain code.
 */
public record DomainSpec(
        String name,
        String slug,
        String functionalPattern,
        String assetType,
        String businessArea,
        String businessDomain,
        String controlRecordName,
        ControlRecordSpec controlRecord,
        List<BehaviourQualifierSpec> behaviourQualifiers) {

    public DomainSpec {
        behaviourQualifiers = List.copyOf(behaviourQualifiers);
    }

    /** URL segment for the control record, e.g. {@code ijara-lease-fulfillment-arrangement}. */
    public String controlRecordSlug() {
        return slugify(controlRecordName);
    }

    public Optional<BehaviourQualifierSpec> behaviourQualifier(String path) {
        return behaviourQualifiers.stream().filter(b -> b.path().equals(path)).findFirst();
    }

    public String readScope() {
        return "isb:" + slug + ":read";
    }

    public String writeScope() {
        return "isb:" + slug + ":write";
    }

    public static String slugify(String text) {
        return text.toLowerCase().replaceAll("[^a-z0-9]+", "-").replaceAll("(^-|-$)", "");
    }
}
