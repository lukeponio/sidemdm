package com.example.personalprofile

import android.app.Activity
import android.app.admin.DevicePolicyManager
import android.content.Intent
import android.os.Bundle
import android.util.Log

/**
 * Handles ACTION_GET_PROVISIONING_MODE during six-tap QR setup (spec 5.2).
 * Returns MANAGED_PROFILE (COPE on a QR-provisioned device) or cancels. No UI.
 */
class ProvisioningModeActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val allowed = intent.getIntegerArrayListExtra(
            DevicePolicyManager.EXTRA_PROVISIONING_ALLOWED_PROVISIONING_MODES
        )
        val mode = ProvisioningPolicy.chooseMode(allowed)
        if (mode == null) {
            Log.w("PersonalProfileDpc", "Managed-profile mode not allowed ($allowed); cancelling")
            setResult(RESULT_CANCELED)
        } else {
            setResult(RESULT_OK, Intent().putExtra(DevicePolicyManager.EXTRA_PROVISIONING_MODE, mode))
        }
        // Do not start any UI or service after returning to Setup Wizard.
        finish()
    }
}
