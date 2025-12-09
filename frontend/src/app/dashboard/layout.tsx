import { ProtectedRoute } from "@/components/auth";

export default function DashboardRootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <ProtectedRoute>{children}</ProtectedRoute>;
}
