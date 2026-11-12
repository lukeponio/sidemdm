package com.example.personalprofile

import android.app.admin.DevicePolicyManager.PROVISIONING_MODE_FULLY_MANAGED_DEVICE
import android.app.admin.DevicePolicyManager.PROVISIONING_MODE_MANAGED_PROFILE
import android.app.admin.DevicePolicyManager.PROVISIONING_MODE_MANAGED_PROFILE_ON_PERSONAL_DEVICE
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ProvisioningPolicyTest {
    @Test fun choosesManagedProfileWhenOffered() {
        val modes = listOf(PROVISIONING_MODE_FULLY_MANAGED_DEVICE, PROVISIONING_MODE_MANAGED_PROFILE)
        assertEquals(PROVISIONING_MODE_MANAGED_PROFILE, ProvisioningPolicy.chooseMode(modes))
    }

    // AT-04: only fully managed allowed -> cancel, never Device Owner.
    @Test fun cancelsWhenOnlyFullyManagedAllowed() {
        assertNull(ProvisioningPolicy.chooseMode(listOf(PROVISIONING_MODE_FULLY_MANAGED_DEVICE)))
    }

    @Test fun cancelsForPersonalDeviceOnlyOrMissingList() {
        assertNull(ProvisioningPolicy.chooseMode(listOf(PROVISIONING_MODE_MANAGED_PROFILE_ON_PERSONAL_DEVICE)))
        assertNull(ProvisioningPolicy.chooseMode(emptyList()))
        assertNull(ProvisioningPolicy.chooseMode(null))
    }

    @Test fun removalOnlyWhenAllPredicatesHold() {
        assertTrue(OwnerState(true, true, true).isVerifiedWorkProfileOwner)
        assertNull(OwnerState(true, true, true).removalBlockReason())
        listOf(
            OwnerState(false, true, true),
            OwnerState(true, false, true),
            OwnerState(true, true, false),
            OwnerState(true, true, true, queryError = "SecurityException"),
        ).forEach {
            assertFalse(it.isVerifiedWorkProfileOwner)
            assertNotNull(it.removalBlockReason())
        }
    }
}
