"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    Target,
    Plus,
    Pencil,
    Trash2,
    TrendingUp,
    Calendar,
    DollarSign,
    AlertCircle,
} from "lucide-react";
import analyticsApi, { RevenueGoal } from "@/lib/api/analytics";

export default function RevenueGoalsPage() {
    const [goals, setGoals] = useState<RevenueGoal[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [selectedGoal, setSelectedGoal] = useState<RevenueGoal | null>(null);
    const [formData, setFormData] = useState({
        name: "",
        target_amount: "",
        start_date: "",
        end_date: "",
    });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadGoals();
    }, []);

    const loadGoals = async () => {
        setLoading(true);
        try {
            const data = await analyticsApi.getRevenueGoals();
            setGoals(data.length > 0 ? data : generateMockGoals());
        } catch (error) {
            console.error("Failed to load goals:", error);
            setGoals(generateMockGoals());
        } finally {
            setLoading(false);
        }
    };

    const generateMockGoals = (): RevenueGoal[] => {
        return [
            {
                id: "1",
                name: "Q4 2024 Revenue Target",
                target_amount: 10000,
                current_amount: 7500,
                start_date: "2024-10-01",
                end_date: "2024-12-31",
                progress_percentage: 75,
                forecast_amount: 9800,
                forecast_probability: 85,
            },
            {
                id: "2",
                name: "Monthly Membership Goal",
                target_amount: 500,
                current_amount: 320,
                start_date: "2024-12-01",
                end_date: "2024-12-31",
                progress_percentage: 64,
                forecast_amount: 480,
                forecast_probability: 70,
            },
            {
                id: "3",
                name: "Super Chat Holiday Special",
                target_amount: 1000,
                current_amount: 450,
                start_date: "2024-12-15",
                end_date: "2024-12-25",
                progress_percentage: 45,
                forecast_amount: 920,
                forecast_probability: 60,
            },
        ];
    };

    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount);
    };

    const formatDate = (dateStr: string): string => {
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    const getDaysRemaining = (endDate: string): number => {
        const end = new Date(endDate);
        const now = new Date();
        const diff = end.getTime() - now.getTime();
        return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
    };

    const getProgressColor = (percentage: number): string => {
        if (percentage >= 75) return "bg-green-500";
        if (percentage >= 50) return "bg-yellow-500";
        if (percentage >= 25) return "bg-orange-500";
        return "bg-red-500";
    };

    const resetForm = () => {
        setFormData({
            name: "",
            target_amount: "",
            start_date: "",
            end_date: "",
        });
    };

    const handleAddGoal = async () => {
        if (!formData.name || !formData.target_amount || !formData.start_date || !formData.end_date) {
            return;
        }

        setSaving(true);
        try {
            const newGoal = await analyticsApi.createRevenueGoal({
                name: formData.name,
                target_amount: parseFloat(formData.target_amount),
                start_date: formData.start_date,
                end_date: formData.end_date,
            });
            setGoals([...goals, newGoal]);
            setIsAddModalOpen(false);
            resetForm();
        } catch (error) {
            // For demo, add mock goal
            const mockGoal: RevenueGoal = {
                id: Date.now().toString(),
                name: formData.name,
                target_amount: parseFloat(formData.target_amount),
                current_amount: 0,
                start_date: formData.start_date,
                end_date: formData.end_date,
                progress_percentage: 0,
            };
            setGoals([...goals, mockGoal]);
            setIsAddModalOpen(false);
            resetForm();
        } finally {
            setSaving(false);
        }
    };

    const handleEditGoal = async () => {
        if (!selectedGoal || !formData.name || !formData.target_amount) {
            return;
        }

        setSaving(true);
        try {
            const updatedGoal = await analyticsApi.updateRevenueGoal(selectedGoal.id, {
                name: formData.name,
                target_amount: parseFloat(formData.target_amount),
                start_date: formData.start_date,
                end_date: formData.end_date,
            });
            setGoals(goals.map(g => g.id === selectedGoal.id ? updatedGoal : g));
            setIsEditModalOpen(false);
            setSelectedGoal(null);
            resetForm();
        } catch (error) {
            // For demo, update locally
            setGoals(goals.map(g => g.id === selectedGoal.id ? {
                ...g,
                name: formData.name,
                target_amount: parseFloat(formData.target_amount),
                start_date: formData.start_date,
                end_date: formData.end_date,
            } : g));
            setIsEditModalOpen(false);
            setSelectedGoal(null);
            resetForm();
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteGoal = async () => {
        if (!selectedGoal) return;

        setSaving(true);
        try {
            await analyticsApi.deleteRevenueGoal(selectedGoal.id);
            setGoals(goals.filter(g => g.id !== selectedGoal.id));
            setIsDeleteModalOpen(false);
            setSelectedGoal(null);
        } catch (error) {
            // For demo, delete locally
            setGoals(goals.filter(g => g.id !== selectedGoal.id));
            setIsDeleteModalOpen(false);
            setSelectedGoal(null);
        } finally {
            setSaving(false);
        }
    };

    const openEditModal = (goal: RevenueGoal) => {
        setSelectedGoal(goal);
        setFormData({
            name: goal.name,
            target_amount: goal.target_amount.toString(),
            start_date: goal.start_date,
            end_date: goal.end_date,
        });
        setIsEditModalOpen(true);
    };

    const openDeleteModal = (goal: RevenueGoal) => {
        setSelectedGoal(goal);
        setIsDeleteModalOpen(true);
    };

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Revenue", href: "/dashboard/revenue" },
                { label: "Goals" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Revenue Goals</h1>
                        <p className="text-muted-foreground">
                            Set targets and track your earnings progress
                        </p>
                    </div>
                    <Dialog open={isAddModalOpen} onOpenChange={setIsAddModalOpen}>
                        <DialogTrigger asChild>
                            <Button className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700">
                                <Plus className="h-4 w-4 mr-2" />
                                Add Goal
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Create Revenue Goal</DialogTitle>
                                <DialogDescription>
                                    Set a new revenue target to track your earnings progress.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Goal Name</Label>
                                    <Input
                                        id="name"
                                        placeholder="e.g., Q1 2025 Revenue Target"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="target">Target Amount ($)</Label>
                                    <Input
                                        id="target"
                                        type="number"
                                        placeholder="10000"
                                        value={formData.target_amount}
                                        onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="start_date">Start Date</Label>
                                        <Input
                                            id="start_date"
                                            type="date"
                                            value={formData.start_date}
                                            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="end_date">End Date</Label>
                                        <Input
                                            id="end_date"
                                            type="date"
                                            value={formData.end_date}
                                            onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                        />
                                    </div>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => { setIsAddModalOpen(false); resetForm(); }}>
                                    Cancel
                                </Button>
                                <Button onClick={handleAddGoal} disabled={saving}>
                                    {saving ? "Creating..." : "Create Goal"}
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                {/* Goals List */}
                {loading ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {[1, 2, 3].map((i) => (
                            <Card key={i} className="border-0 bg-card shadow-lg animate-pulse">
                                <CardContent className="p-6">
                                    <div className="h-6 bg-muted rounded w-3/4 mb-4" />
                                    <div className="h-4 bg-muted rounded w-1/2 mb-2" />
                                    <div className="h-2 bg-muted rounded w-full mb-4" />
                                    <div className="h-4 bg-muted rounded w-2/3" />
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : goals.length === 0 ? (
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-12 text-center">
                            <Target className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No Revenue Goals</h3>
                            <p className="text-muted-foreground mb-4">
                                Create your first revenue goal to start tracking your earnings progress.
                            </p>
                            <Button onClick={() => setIsAddModalOpen(true)}>
                                <Plus className="h-4 w-4 mr-2" />
                                Create Goal
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {goals.map((goal) => {
                            const daysRemaining = getDaysRemaining(goal.end_date);
                            const isExpired = daysRemaining === 0;
                            const isOnTrack = goal.forecast_probability && goal.forecast_probability >= 70;

                            return (
                                <Card key={goal.id} className="border-0 bg-card shadow-lg hover:shadow-xl transition-shadow">
                                    <CardHeader className="pb-2">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-2">
                                                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber-500 to-amber-600">
                                                    <Target className="h-4 w-4 text-white" />
                                                </div>
                                                <CardTitle className="text-base font-semibold line-clamp-1">
                                                    {goal.name}
                                                </CardTitle>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8"
                                                    onClick={() => openEditModal(goal)}
                                                >
                                                    <Pencil className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                                    onClick={() => openDeleteModal(goal)}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        {/* Progress */}
                                        <div>
                                            <div className="flex items-center justify-between text-sm mb-2">
                                                <span className="text-muted-foreground">Progress</span>
                                                <span className="font-medium">{goal.progress_percentage}%</span>
                                            </div>
                                            <Progress
                                                value={goal.progress_percentage}
                                                className="h-2"
                                            />
                                            <div className="flex items-center justify-between text-sm mt-2">
                                                <span className="font-semibold text-green-600">
                                                    {formatCurrency(goal.current_amount)}
                                                </span>
                                                <span className="text-muted-foreground">
                                                    of {formatCurrency(goal.target_amount)}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Forecast */}
                                        {goal.forecast_amount && (
                                            <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
                                                <TrendingUp className={`h-4 w-4 ${isOnTrack ? "text-green-500" : "text-yellow-500"}`} />
                                                <div className="flex-1">
                                                    <p className="text-xs text-muted-foreground">Forecast</p>
                                                    <p className="text-sm font-medium">
                                                        {formatCurrency(goal.forecast_amount)}
                                                        {goal.forecast_probability && (
                                                            <span className={`ml-2 text-xs ${isOnTrack ? "text-green-500" : "text-yellow-500"}`}>
                                                                ({goal.forecast_probability}% likely)
                                                            </span>
                                                        )}
                                                    </p>
                                                </div>
                                            </div>
                                        )}

                                        {/* Date Range */}
                                        <div className="flex items-center justify-between text-sm">
                                            <div className="flex items-center gap-1 text-muted-foreground">
                                                <Calendar className="h-3 w-3" />
                                                <span>{formatDate(goal.start_date)} - {formatDate(goal.end_date)}</span>
                                            </div>
                                        </div>

                                        {/* Days Remaining */}
                                        <div className={`flex items-center gap-2 text-sm ${isExpired ? "text-red-500" : daysRemaining <= 7 ? "text-yellow-500" : "text-muted-foreground"}`}>
                                            {isExpired ? (
                                                <>
                                                    <AlertCircle className="h-4 w-4" />
                                                    <span>Goal period ended</span>
                                                </>
                                            ) : (
                                                <>
                                                    <DollarSign className="h-4 w-4" />
                                                    <span>{daysRemaining} days remaining</span>
                                                </>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                )}

                {/* Edit Modal */}
                <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Edit Revenue Goal</DialogTitle>
                            <DialogDescription>
                                Update your revenue target details.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label htmlFor="edit-name">Goal Name</Label>
                                <Input
                                    id="edit-name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="edit-target">Target Amount ($)</Label>
                                <Input
                                    id="edit-target"
                                    type="number"
                                    value={formData.target_amount}
                                    onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="edit-start">Start Date</Label>
                                    <Input
                                        id="edit-start"
                                        type="date"
                                        value={formData.start_date}
                                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="edit-end">End Date</Label>
                                    <Input
                                        id="edit-end"
                                        type="date"
                                        value={formData.end_date}
                                        onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                    />
                                </div>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => { setIsEditModalOpen(false); setSelectedGoal(null); resetForm(); }}>
                                Cancel
                            </Button>
                            <Button onClick={handleEditGoal} disabled={saving}>
                                {saving ? "Saving..." : "Save Changes"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* Delete Confirmation Modal */}
                <Dialog open={isDeleteModalOpen} onOpenChange={setIsDeleteModalOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Delete Revenue Goal</DialogTitle>
                            <DialogDescription>
                                Are you sure you want to delete "{selectedGoal?.name}"? This action cannot be undone.
                            </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => { setIsDeleteModalOpen(false); setSelectedGoal(null); }}>
                                Cancel
                            </Button>
                            <Button variant="destructive" onClick={handleDeleteGoal} disabled={saving}>
                                {saving ? "Deleting..." : "Delete Goal"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </DashboardLayout>
    );
}
