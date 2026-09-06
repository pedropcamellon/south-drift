"use client";

import React from "react";

import { motion } from "framer-motion";
import { Info } from "lucide-react";
import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import useSWR from "swr";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";

import { API_ENDPOINTS, fetcher } from "@/lib/api";

export default function MetricsCards() {
    // TODO: Implement dashboard metrics endpoint in FastAPI
    const { data, error, isLoading } = useSWR<{
        totalPatients: number;
        recentPatients: Array<{ month: string; count: number }>;
    }>(null, fetcher);
    const [open, setOpen] = React.useState(false);

    return (
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Total Patients Card (left half) */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="h-full"
            >
                <Card className="p-6 flex flex-col items-start w-full h-full justify-between relative">
                    <div className="flex w-full justify-between items-start mb-1">
                        <span className="text-base font-bold text-slate-700">
                            Total Patients
                        </span>
                        <Dialog open={open} onOpenChange={setOpen}>
                            <DialogTrigger asChild>
                                <Button
                                    variant="ghost"
                                    size="icon-md"
                                    aria-label="Show patient history chart"
                                >
                                    <Info className="w-5 h-5" />
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-xl">
                                <DialogHeader>
                                    <DialogTitle>
                                        Patients (Last 8 Weeks)
                                    </DialogTitle>
                                    <span className="text-green-600 text-xs mt-2 flex items-center">
                                        ▲ 2.1%{" "}
                                        <span className="ml-1 text-slate-400">
                                            Since last month
                                        </span>
                                    </span>
                                </DialogHeader>
                                <div className="w-full h-64 mt-4">
                                    <ResponsiveContainer
                                        width="100%"
                                        height="100%"
                                    >
                                        <LineChart
                                            data={data?.recentPatients || []}
                                            margin={{
                                                top: 10,
                                                right: 30,
                                                left: 0,
                                                bottom: 0,
                                            }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis
                                                dataKey="month"
                                                tick={{ fontSize: 12 }}
                                            />
                                            <YAxis allowDecimals={false} />
                                            <Tooltip />
                                            <Line
                                                type="monotone"
                                                dataKey="count"
                                                stroke="#4A90E2"
                                                strokeWidth={3}
                                                dot={{ r: 5 }}
                                                activeDot={{ r: 7 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </DialogContent>
                        </Dialog>
                    </div>
                    <span className="text-3xl font-bold text-blue-700">
                        {isLoading ? (
                            <span className="animate-pulse">...</span>
                        ) : (
                            (data?.totalPatients ?? 0)
                        )}
                    </span>
                    <span className="text-green-600 text-xs mt-2 flex items-center">
                        ▲ 2.1%{" "}
                        <span className="ml-1 text-slate-400">
                            Since last month
                        </span>
                    </span>
                </Card>
            </motion.div>
            {/* Recent Patients Card (right half) */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7 }}
                className="h-full"
            >
                <Card className="p-6 flex flex-col items-start w-full h-full justify-between">
                    <span className="text-base font-bold text-slate-700 mb-1">
                        Recent Patients
                    </span>
                    <span className="text-3xl font-bold text-blue-700">
                        {isLoading ? (
                            <span className="animate-pulse">...</span>
                        ) : (
                            (data?.recentPatients ?? []).reduce(
                                (total, patient) => total + patient.count,
                                0
                            )
                        )}
                    </span>
                </Card>
            </motion.div>
        </section>
    );
}
