import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

import type { EncounterFormData } from "@/hooks/useEncounterForm";

import { ENCOUNTER_TYPES } from "@/constants/encounters";

interface EncounterFormProps {
    formData: EncounterFormData;
    onChange: (field: keyof EncounterFormData, value: string) => void;
    error: string | null;
}

export function EncounterForm({
    formData,
    onChange,
    error,
}: EncounterFormProps) {
    return (
        <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                    <Label htmlFor="encounterType">Type</Label>
                    <Select
                        value={formData.encounterType}
                        onValueChange={(value) =>
                            onChange("encounterType", value)
                        }
                    >
                        <SelectTrigger id="encounterType">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            {ENCOUNTER_TYPES.map((encounterType) => (
                                <SelectItem
                                    key={encounterType.value}
                                    value={encounterType.value}
                                >
                                    {encounterType.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
                <div className="space-y-2">
                    <Label htmlFor="startedAt">Date and time</Label>
                    <Input
                        id="startedAt"
                        type="datetime-local"
                        value={formData.startedAt}
                        onChange={(event) =>
                            onChange("startedAt", event.target.value)
                        }
                        required
                    />
                </div>
            </div>
            <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                    id="title"
                    value={formData.title}
                    onChange={(event) => onChange("title", event.target.value)}
                    required
                />
            </div>
            <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(event) =>
                        onChange("description", event.target.value)
                    }
                    rows={3}
                />
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                    <Label htmlFor="location">Location</Label>
                    <Input
                        id="location"
                        value={formData.location}
                        onChange={(event) =>
                            onChange("location", event.target.value)
                        }
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="clinicianName">Clinician name</Label>
                    <Input
                        id="clinicianName"
                        value={formData.clinicianName}
                        onChange={(event) =>
                            onChange("clinicianName", event.target.value)
                        }
                    />
                </div>
            </div>
            <div className="space-y-2">
                <Label htmlFor="clinicianId">Clinician ID</Label>
                <Input
                    id="clinicianId"
                    value={formData.clinicianId}
                    onChange={(event) =>
                        onChange("clinicianId", event.target.value)
                    }
                />
            </div>
            {error ? (
                <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
                    {error}
                </p>
            ) : null}
        </div>
    );
}
