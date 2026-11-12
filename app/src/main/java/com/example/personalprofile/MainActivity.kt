package com.example.personalprofile

import android.app.Activity
import android.app.AlertDialog
import android.os.Build
import android.os.Bundle
import android.util.TypedValue
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * Status screen plus the guarded Remove Work Profile action (spec 7.1).
 * The button only exists when every safety predicate holds; removal needs two confirmations.
 */
class MainActivity : Activity() {
    private lateinit var roleView: TextView
    private lateinit var stateView: TextView
    private lateinit var reasonView: TextView
    private lateinit var removeButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val pad = dp(24)
        val column = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
        }
        fun text(size: Float, value: String = "") = TextView(this).apply {
            setTextSize(TypedValue.COMPLEX_UNIT_SP, size)
            text = value
            setPadding(0, 0, 0, dp(12))
            column.addView(this)
        }
        text(24f, "Work Profile")
        text(16f, "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
        roleView = text(18f)
        stateView = text(18f)
        reasonView = text(14f)
        removeButton = Button(this).apply {
            text = "Remove Work Profile"
            setOnClickListener { confirmStepOne() }
            column.addView(this)
        }
        setContentView(ScrollView(this).apply { addView(column) })
    }

    override fun onResume() {
        super.onResume()
        render()
    }

    private fun render() {
        val state = RemoveProfileController.readState(this)
        val verified = state.isVerifiedWorkProfileOwner
        roleView.text = "Role: " + if (verified) "WORK PROFILE OWNER" else "NOT MANAGED"
        stateView.text = "State: " + if (verified) "Active" else "Unsupported"
        reasonView.text = state.removalBlockReason() ?: ""
        // AT-06: outside a verified work profile the action is not offered at all.
        removeButton.visibility = if (verified) View.VISIBLE else View.GONE
    }

    private fun confirmStepOne() {
        AlertDialog.Builder(this)
            .setTitle("Remove work profile?")
            .setMessage(
                "This permanently deletes the work profile and all its apps and data. " +
                    "Your personal profile should remain.\n\nWork data cannot be recovered."
            )
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Continue") { _, _ -> confirmStepTwo() }
            .show()
    }

    private fun confirmStepTwo() {
        AlertDialog.Builder(this)
            .setTitle("Are you sure?")
            .setMessage("Last step. Tap Remove Work Profile to delete all work apps, accounts and files now.")
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Remove Work Profile") { _, _ -> remove() }
            .show()
    }

    private fun remove() {
        when (val outcome = RemoveProfileController.removeWorkProfile(this)) {
            RemoveProfileController.Outcome.Removing -> finish()
            is RemoveProfileController.Outcome.Refused ->
                AlertDialog.Builder(this)
                    .setTitle("Work profile not removed")
                    .setMessage(outcome.reason)
                    .setPositiveButton("Close") { _, _ -> render() }
                    .show()
        }
    }

    private fun dp(v: Int) = TypedValue.applyDimension(
        TypedValue.COMPLEX_UNIT_DIP, v.toFloat(), resources.displayMetrics
    ).toInt()
}
