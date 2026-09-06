import { User, UserRole } from "@/types/user";

export const permissions = {
    patientsRead: "patients:read",
    patientsCreate: "patients:create",
    patientsUpdate: "patients:update",
    patientsDelete: "patients:delete",
    encountersRead: "encounters:read",
    encountersCreate: "encounters:create",
    encountersUpdate: "encounters:update",
    encountersDelete: "encounters:delete",
    encountersSummarize: "encounters:summarize",
    documentsRead: "documents:read",
    documentsCreate: "documents:create",
    documentsUpdate: "documents:update",
    documentsDelete: "documents:delete",
    voiceRecord: "voice:record",
    voiceReview: "voice:review",
    usersRead: "users:read",
    usersUpdate: "users:update",
    adminHealthRead: "admin:health:read",
    portalRead: "portal:read",
} as const;

export type Permission = (typeof permissions)[keyof typeof permissions];

const allPermissions = new Set<Permission>(Object.values(permissions));

const rolePermissions: Record<UserRole, Set<Permission>> = {
    [UserRole.ADMIN]: new Set(allPermissions),
    [UserRole.PROVIDER]: new Set([
        permissions.patientsRead,
        permissions.patientsCreate,
        permissions.patientsUpdate,
        permissions.patientsDelete,
        permissions.encountersRead,
        permissions.encountersCreate,
        permissions.encountersUpdate,
        permissions.encountersDelete,
        permissions.encountersSummarize,
        permissions.documentsRead,
        permissions.documentsCreate,
        permissions.documentsUpdate,
        permissions.documentsDelete,
        permissions.voiceRecord,
        permissions.voiceReview,
    ]),
    [UserRole.STAFF]: new Set([
        permissions.patientsRead,
        permissions.patientsCreate,
        permissions.patientsUpdate,
        permissions.encountersRead,
        permissions.encountersCreate,
        permissions.encountersUpdate,
        permissions.voiceRecord,
        permissions.voiceReview,
    ]),
    [UserRole.PATIENT]: new Set([permissions.portalRead]),
};

export function hasPermission(
    user: User | null,
    permission: Permission
): boolean {
    if (!user) {
        return false;
    }

    return rolePermissions[user.role]?.has(permission) ?? false;
}

export function hasAnyPermission(
    user: User | null,
    requiredPermissions: Permission[]
): boolean {
    if (requiredPermissions.length === 0) {
        return true;
    }

    return requiredPermissions.some((permission) =>
        hasPermission(user, permission)
    );
}

export function getRoleLabel(role: UserRole): string {
    switch (role) {
        case UserRole.ADMIN:
            return "Admin";
        case UserRole.PROVIDER:
            return "Provider";
        case UserRole.STAFF:
            return "Receptionist";
        case UserRole.PATIENT:
            return "Patient";
        default:
            return role;
    }
}
