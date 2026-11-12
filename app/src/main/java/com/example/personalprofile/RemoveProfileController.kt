package com.example.personalprofile

import android.app.admin.DevicePolicyManager
import android.content.Context
import android.os.UserManager
import android.util.Log

/**
 * The only code path that can delete anything. It deletes the WORK profile only:
 * it calls wipeData(0, reason) on this profile's own DevicePolicyManager, never on the
 * parent-profile instance, never the device-wide wipe API, never by clearing profile ownership (FR-08, FR-09, 6.1).
 */
object RemoveProfileController {
    private const val TAG = "PersonalProfileDpc"
    private const val WIPE_REASON = "Remove managed work profile"

    sealed interface Outcome {
        /** wipeData was accepted; the system is now removing the work profile. */
        data object Removing : Outcome
        /** Nothing was wiped. [reason] is safe to show to the user. */
        data class Refused(val reason: String) : Outcome
    }

    fun readState(context: Context): OwnerState {
        val dpm = context.getSystemService(DevicePolicyManager::class.java)
        return try {
            OwnerState(
                isProfileOwner = dpm.isProfileOwnerApp(context.packageName),
                // UserManager's check needs no admin rights; DPM.isManagedProfile(admin) throws
                // SecurityException in the personal copy, which hid the real reason from the user.
                isManagedProfile = context.getSystemService(UserManager::class.java).isManagedProfile,
                isOrgOwnedManagedProfile = dpm.isOrganizationOwnedDeviceWithManagedProfile,
            )
        } catch (e: Exception) {
            // Fail closed: an exception means "not verified", never "try another API".
            OwnerState(false, false, false, queryError = e.javaClass.simpleName)
        }
    }

    /** Call only after the user has passed both confirmation steps in the UI (FR-10). */
    fun removeWorkProfile(context: Context): Outcome {
        // Re-check right before the destructive call; never trust state read earlier.
        val state = readState(context)
        state.removalBlockReason()?.let {
            Log.w(TAG, "Removal refused: safety predicate failed")
            return Outcome.Refused(it)
        }
        val dpm = context.getSystemService(DevicePolicyManager::class.java)
        return try {
            dpm.wipeData(0, WIPE_REASON)
            Log.i(TAG, "wipeData accepted for managed profile")
            Outcome.Removing
        } catch (e: Exception) {
            Log.e(TAG, "wipeData failed: ${e.javaClass.simpleName}")
            // No fallback to any other wipe API (spec 7.2).
            Outcome.Refused("Android refused to remove the work profile (${e.javaClass.simpleName}). Nothing was deleted by this app.")
        }
    }
}
