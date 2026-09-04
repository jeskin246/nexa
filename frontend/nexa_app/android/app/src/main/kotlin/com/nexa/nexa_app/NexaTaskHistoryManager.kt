package com.nexa.nexa_app

import android.content.Context
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject

object NexaTaskHistoryManager {
    private const val TAG = "NexaTaskHistoryManager"
    private const val PREF_NAME = "nexa_task_history_prefs"
    private const val KEY_HISTORY = "task_history_log"

    fun logStateTransition(
        context: Context,
        taskId: String,
        executionId: String,
        status: String,
        recipient: String,
        message: String,
        details: String
    ) {
        try {
            val prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
            val existingJson = prefs.getString(KEY_HISTORY, "[]") ?: "[]"
            val jsonArray = JSONArray(existingJson)

            val entry = JSONObject().apply {
                put("taskId", taskId)
                put("executionId", executionId)
                put("status", status)
                put("recipient", recipient)
                put("message", message)
                put("details", details)
                put("timestamp", System.currentTimeMillis())
            }

            val trimmedArray = JSONArray()
            trimmedArray.put(entry)
            val limit = if (jsonArray.length() > 99) 99 else jsonArray.length()
            for (i in 0 until limit) {
                trimmedArray.put(jsonArray.get(i))
            }

            prefs.edit().putString(KEY_HISTORY, trimmedArray.toString()).apply()
            Log.i(TAG, "History logged: taskId=$taskId -> status=$status ($details)")
        } catch (e: Exception) {
            Log.e(TAG, "Error logging task history: ${e.message}")
        }
    }
}
