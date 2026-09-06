"use client";

import { useEffect, useState } from "react";

import { FileSearch, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

import { API_ENDPOINTS, apiJson, apiRequest } from "@/lib/api";

import { ChartReview } from "@/types";

import { CHART_REVIEW_STATUS } from "@/constants/chartReview";

interface ChartReviewSectionProps {
    encounterId: string;
}

export function ChartReviewSection({ encounterId }: ChartReviewSectionProps) {
    const [review, setReview] = useState<ChartReview | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRequesting, setIsRequesting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let active = true;

        async function loadReview() {
            setIsLoading(true);
            setError(null);
            try {
                const response = await apiRequest(
                    API_ENDPOINTS.encounterChartReview(encounterId)
                );
                if (response.status === 404 || response.status === 204) {
                    return;
                }
                if (!response.ok) {
                    throw new Error("Unable to load chart review.");
                }
                const data = (await response.json()) as ChartReview | null;
                if (active) {
                    setReview(data);
                }
            } catch {
                if (active) {
                    setError("Chart review is currently unavailable.");
                }
            } finally {
                if (active) {
                    setIsLoading(false);
                }
            }
        }

        void loadReview();
        return () => {
            active = false;
        };
    }, [encounterId]);

    useEffect(() => {
        if (
            review?.status !== CHART_REVIEW_STATUS.QUEUED &&
            review?.status !== CHART_REVIEW_STATUS.RUNNING
        ) {
            return;
        }

        const interval = window.setInterval(async () => {
            try {
                const data = await apiJson<ChartReview | null>(
                    API_ENDPOINTS.encounterChartReview(encounterId)
                );
                setReview(data);
            } catch {
                setError("Unable to refresh chart review status.");
            }
        }, 2_000);

        return () => window.clearInterval(interval);
    }, [encounterId, review?.status]);

    async function requestReview() {
        setIsRequesting(true);
        setError(null);
        try {
            const data = await apiJson<ChartReview>(
                API_ENDPOINTS.encounterChartReview(encounterId),
                { method: "POST" }
            );
            setReview(data);
        } catch {
            setError("Unable to generate the draft review.");
        } finally {
            setIsRequesting(false);
        }
    }

    const canRequest =
        !isLoading &&
        !isRequesting &&
        review?.status !== CHART_REVIEW_STATUS.QUEUED &&
        review?.status !== CHART_REVIEW_STATUS.RUNNING;

    return (
        <section
            className="border-t pt-4"
            aria-labelledby="chart-review-heading"
        >
            <div className="flex items-center justify-between gap-3">
                <div>
                    <h3
                        id="chart-review-heading"
                        className="text-sm font-semibold"
                    >
                        Chart Review Draft
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        Draft support based on the selected encounter and
                        available chart context.
                    </p>
                </div>
                <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={requestReview}
                    disabled={!canRequest}
                    isLoading={isRequesting}
                    loadingText="Generating"
                >
                    {review ? (
                        <RefreshCw aria-hidden="true" />
                    ) : (
                        <FileSearch aria-hidden="true" />
                    )}
                    {review ? "Generate new draft" : "Generate draft"}
                </Button>
            </div>

            {error ? (
                <p className="mt-3 text-sm text-destructive">{error}</p>
            ) : null}
            {isLoading ? (
                <p className="mt-3 text-sm text-muted-foreground">
                    Loading review...
                </p>
            ) : null}
            {review?.status === CHART_REVIEW_STATUS.FAILED ? (
                <p className="mt-3 text-sm text-destructive">
                    {review.failureMessage ||
                        "The draft review could not be completed."}
                </p>
            ) : null}
            {review?.status === CHART_REVIEW_STATUS.QUEUED ||
            review?.status === CHART_REVIEW_STATUS.RUNNING ? (
                <p className="mt-3 text-sm text-muted-foreground">
                    Draft review is processing.
                </p>
            ) : null}
            {review?.status === CHART_REVIEW_STATUS.COMPLETED ? (
                <div className="mt-3 space-y-3 text-sm">
                    <p>{review.summary}</p>
                    {review.reasoning ? (
                        <div>
                            <h4 className="font-medium">Review rationale</h4>
                            <p className="mt-1 text-muted-foreground">
                                {review.reasoning}
                            </p>
                        </div>
                    ) : null}
                    <div className="grid gap-3 sm:grid-cols-2">
                        <ReviewList
                            title="Missing information"
                            items={review.missingInfo}
                        />
                        <ReviewList
                            title="Follow-up questions"
                            items={review.followUpQuestions}
                        />
                    </div>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground">
                        <span>
                            Confidence: {review.confidence ?? "Not available"}
                        </span>
                        <span>Sources: {review.sourceRefs.length}</span>
                    </div>
                    {review.sourceRefs.length ? (
                        <div>
                            <h4 className="font-medium">Source references</h4>
                            <ul className="mt-1 space-y-1 text-xs text-muted-foreground">
                                {review.sourceRefs.map((sourceRef) => (
                                    <li
                                        key={`${sourceRef.sourceType}-${sourceRef.resourceId}-${sourceRef.contentRole}`}
                                    >
                                        {formatSourceReference(sourceRef)}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ) : null}
                    {review.reviewFlags.length ? (
                        <ReviewList
                            title="Review flags"
                            items={review.reviewFlags}
                        />
                    ) : null}
                </div>
            ) : null}
        </section>
    );
}

function formatSourceReference(
    sourceRef: ChartReview["sourceRefs"][number]
): string {
    const date = sourceRef.occurredAt
        ? new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(
              new Date(sourceRef.occurredAt)
          )
        : null;
    const label = sourceRef.displayLabel || "Referenced chart source";
    const role = sourceRef.contentRole || sourceRef.sourceType;
    return [date, label, role].filter(Boolean).join(" - ");
}

function ReviewList({ title, items }: { title: string; items: string[] }) {
    if (!items.length) {
        return null;
    }

    return (
        <div>
            <h4 className="font-medium">{title}</h4>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-muted-foreground">
                {items.map((item) => (
                    <li key={item}>{item}</li>
                ))}
            </ul>
        </div>
    );
}
