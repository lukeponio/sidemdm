package com.example.personalprofile

import android.app.admin.DeviceAdminReceiver
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * Device-admin receiver named in the provisioning QR
 * ("com.example.personalprofile/.AdminReceiver"). Its only job beyond being the admin is to switch
 * the new work profile on: Android leaves a managed profile disabled (no Work tab) until its owner
 * calls setProfileEnabled().
 */
class AdminReceiver : DeviceAdminReceiver() {

    override fun onProfileProvisioningComplete(context: Context, intent: Intent) {
        enableWorkProfile(context)
    }

    override fun onReceive(context: Context, intent: Intent) {
        // Recovery for profiles created by 1.0.0, which never enabled the profile.
        if (intent.action == Intent.ACTION_MY_PACKAGE_REPLACED) enableWorkProfile(context)
        else super.onReceive(context, intent)
    }

    companion object {
        fun component(context: Context): ComponentName =
            ComponentName(context, AdminReceiver::class.java)

        /** Enables the profile only when this copy verifiably owns a managed profile; otherwise no-op. */
        fun enableWorkProfile(context: Context) {
            val state = RemoveProfileController.readState(context)
            if (!state.isProfileOwner || !state.isManagedProfile) return
            try {
                val dpm = context.getSystemService(DevicePolicyManager::class.java)
                dpm.setProfileName(component(context), "Work profile")
                dpm.setProfileEnabled(component(context))
                Log.i("PersonalProfileDpc", "Work profile enabled")
            } catch (e: Exception) {
                Log.e("PersonalProfileDpc", "setProfileEnabled failed: ${e.javaClass.simpleName}")
            }
        }
    }
}
