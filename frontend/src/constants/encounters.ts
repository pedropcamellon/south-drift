import type { EncounterType } from "@/types";

export const ENCOUNTER_TYPES: Array<{ value: EncounterType; label: string }> = [
    { value: "outpatient", label: "Outpatient" },
    { value: "telehealth", label: "Telehealth" },
    { value: "telephone", label: "Telephone" },
    { value: "portal", label: "Portal message" },
    { value: "emergency", label: "Emergency" },
    { value: "inpatient", label: "Inpatient" },
];
