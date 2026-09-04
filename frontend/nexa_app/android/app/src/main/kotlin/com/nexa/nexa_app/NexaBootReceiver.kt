package com.nexa.nexa_app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class NexaBootReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "NexaBootReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        if (action == Intent.ACTION_BOOT_COMPLETED || action == Intent.ACTION_MY_PACKAGE_REPLACED) {
            Log.i(TAG, "BOOT_COMPLETED / PACKAGE_REPLACED received. Restarting Nexa Scheduler & Task Recovery Engine...")
            NexaTaskService.restoreScheduledTasksAfterBoot(context)
        }
    }
}
