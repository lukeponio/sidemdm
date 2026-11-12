package com.example.personalprofile

import android.app.Activity
import android.os.Bundle
import android.util.Log

/**
 * Handles ACTION_ADMIN_POLICY_COMPLIANCE inside the new work profile (spec 5.3, FR-05).
 * Succeeds only when this app is the Profile Owner of an organization-owned managed profile.
 * A mismatch fails enrollment; it never claims device ownership or wipes anything.
 */
class PolicyComplianceActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val state = RemoveProfileController.readState(this)
        if (state.isVerifiedWorkProfileOwner) {
            // Belt and braces: also enable here in case PROFILE_PROVISIONING_COMPLETE is not delivered.
            AdminReceiver.enableWorkProfile(this)
            setResult(RESULT_OK)
        } else {
            Log.w("PersonalProfileDpc", "Compliance check failed: ${state.removalBlockReason()}")
            setResult(RESULT_CANCELED)
        }
        finish()
    }
}
