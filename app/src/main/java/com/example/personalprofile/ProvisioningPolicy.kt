package com.example.personalprofile

import android.app.admin.DevicePolicyManager

/** Pure decision logic, kept free of Android runtime calls so it can be unit tested (AT-04). */
object ProvisioningPolicy {

    /**
     * Returns the provisioning mode to hand back to Setup Wizard, or null to cancel.
     * Only PROVISIONING_MODE_MANAGED_PROFILE is ever chosen (FR-03); FULLY_MANAGED_DEVICE is
     * never substituted (FR-04). A missing allowed-modes list also cancels (fail closed).
     */
    fun chooseMode(allowedModes: List<Int>?): Int? =
        if (allowedModes != null &&
            DevicePolicyManager.PROVISIONING_MODE_MANAGED_PROFILE in allowedModes
        ) {
            DevicePolicyManager.PROVISIONING_MODE_MANAGED_PROFILE
        } else {
            null
        }
}

/** Snapshot of this app's management role in the current user. */
data class OwnerState(
    val isProfileOwner: Boolean,
    val isManagedProfile: Boolean,
    val isOrgOwnedManagedProfile: Boolean,
    /** Set when any platform query threw; the state is then untrusted. */
    val queryError: String? = null,
) {
    /** True only when every safety predicate in spec 6.1 holds (FR-07, FR-12). */
    val isVerifiedWorkProfileOwner: Boolean
        get() = queryError == null && isProfileOwner && isManagedProfile && isOrgOwnedManagedProfile

    /** User-facing reason the removal action is unavailable, or null when it is allowed. */
    fun removalBlockReason(): String? = when {
        queryError != null -> "Could not verify management state ($queryError)."
        !isManagedProfile -> "This copy of the app is not running inside the work profile."
        !isProfileOwner -> "This app is not the owner of this work profile."
        !isOrgOwnedManagedProfile ->
            "The work profile is not in the expected organization-owned (QR setup) mode."
        else -> null
    }
}
