"use client";

import DashboardLayout from "@/components/dashboard/DashboardLayout";
import MetricsCards from "@/components/dashboard/widgets/MetricsCards";
import PatientsSection from "@/components/dashboard/widgets/PatientsSection";
import { Card } from "@/components/ui/card";

import { permissions } from "@/lib/permissions";

export default function ProviderPage() {
    return (
        <DashboardLayout
            requiredPermissions={[permissions.encountersSummarize]}
        >
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">
                    Provider Portal
                </h1>
                <p className="mt-1 text-gray-600">
                    Clinical workbench for chart review, voice notes, and
                    patient follow-up.
                </p>
            </div>
            <div className="mb-8 grid gap-6 md:grid-cols-3">
                <Card className="p-5">
                    <div className="text-sm font-medium text-slate-500">
                        Role View
                    </div>
                    <div className="mt-3 text-2xl font-semibold text-slate-900">
                        Provider
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                        Full clinical access to patients, notes, voice workflow,
                        and documents.
                    </p>
                </Card>
                <Card className="p-5">
                    <div className="text-sm font-medium text-slate-500">
                        Priority
                    </div>
                    <div className="mt-3 text-2xl font-semibold text-slate-900">
                        Golden Workflow
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                        Capture audio, review transcription, and convert notes
                        into structured clinical output.
                    </p>
                </Card>
                <Card className="p-5">
                    <div className="text-sm font-medium text-slate-500">
                        Access Control
                    </div>
                    <div className="mt-3 text-2xl font-semibold text-slate-900">
                        Role-aware
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                        Clinical tools and navigation are filtered to provider
                        responsibilities and permissions.
                    </p>
                </Card>
            </div>
            <MetricsCards />
            <PatientsSection description="Manage patient records and launch the clinical documentation workflow." />
        </DashboardLayout>
    );
}
