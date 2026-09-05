package com.nexa.nexa_app

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Context
import android.content.Intent
import android.graphics.Path
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.util.DisplayMetrics
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

class NexoGestureUnlockService : AccessibilityService() {

    companion object {
        private const val TAG = "NexoGestureUnlockService"
        private const val LOG_TAG = "NEXA_SCHED"

        var instance: NexoGestureUnlockService? = null
        var lastClickTime: Long = 0
        var activePendingContactName: String? = null

        fun isServiceRunning(): Boolean = instance != null

        fun wasSendButtonClickedRecently(withinMs: Long = 10000): Boolean {
            val elapsed = System.currentTimeMillis() - lastClickTime
            return elapsed in 0..withinMs
        }

        fun openAccessibilitySettings(context: Context) {
            try {
                val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                context.startActivity(intent)
            } catch (e: Exception) {
                Log.e(TAG, "Error opening Accessibility Settings: ${e.message}")
            }
        }
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.d(TAG, "NexoGestureUnlockService connected and operational!")
    }

    override fun onDestroy() {
        instance = null
        super.onDestroy()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        val pkgName = event.packageName?.toString() ?: return

        // Auto-send WhatsApp message when WhatsApp or WhatsApp Business comes to foreground
        if (pkgName == "com.whatsapp" || pkgName == "com.whatsapp.w4b") {
            val now = System.currentTimeMillis()
            if (now - lastClickTime < 2500) return

            attemptWhatsAppSendWithRetry()
        }
    }

    private fun attemptWhatsAppSendWithRetry() {
        val handler = Handler(Looper.getMainLooper())
        val delays = listOf(100L, 500L, 1200L, 2200L, 3500L, 5000L)

        for (delay in delays) {
            handler.postDelayed({
                if (System.currentTimeMillis() - lastClickTime > 2500) {
                    val clicked = autoClickWhatsAppSendButton()
                    if (clicked) {
                        lastClickTime = System.currentTimeMillis()
                        Log.i(TAG, "WhatsApp Send button successfully clicked! ✓")
                    } else {
                        // If Send button not directly found, attempt searching contact name if present
                        activePendingContactName?.let { contact ->
                            performContactSearchAndSelect(contact)
                        }
                    }
                }
            }, delay)
        }
    }

    private fun autoClickWhatsAppSendButton(): Boolean {
        val rootNode = rootInActiveWindow ?: return false
        try {
            // Strategy 1: Find by resource ID (com.whatsapp:id/send or com.whatsapp.w4b:id/send)
            val sendById = rootNode.findAccessibilityNodeInfosByViewId("com.whatsapp:id/send")
                .ifEmpty { rootNode.findAccessibilityNodeInfosByViewId("com.whatsapp.w4b:id/send") }

            if (sendById != null && sendById.isNotEmpty()) {
                for (node in sendById) {
                    if (node.isClickable && node.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                        Log.i(TAG, "Successfully auto-clicked WhatsApp Send button by View ID ✓")
                        return true
                    }
                    val parent = node.parent
                    if (parent != null && parent.isClickable && parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                        Log.i(TAG, "Successfully auto-clicked WhatsApp Send button parent by View ID ✓")
                        return true
                    }
                }
            }

            // Strategy 2: Find by Content Description ("Send", "send")
            val sendByText = rootNode.findAccessibilityNodeInfosByText("Send")
                .ifEmpty { rootNode.findAccessibilityNodeInfosByText("send") }

            if (sendByText != null && sendByText.isNotEmpty()) {
                for (node in sendByText) {
                    if (node.isClickable && node.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                        Log.i(TAG, "Successfully auto-clicked WhatsApp Send button by Text ✓")
                        return true
                    }
                    val parent = node.parent
                    if (parent != null && parent.isClickable && parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                        Log.i(TAG, "Successfully auto-clicked WhatsApp Send button parent by Text ✓")
                        return true
                    }
                }
            }

            // Strategy 3: Recursive search for send icon/button
            return searchAndClickSendNode(rootNode)
        } catch (e: Exception) {
            Log.e(TAG, "Error auto-clicking WhatsApp send button: ${e.message}")
            return false
        }
    }

    private fun performContactSearchAndSelect(contactName: String): Boolean {
        val rootNode = rootInActiveWindow ?: return false
        try {
            // Find search button icon in WhatsApp header
            val searchNodes = rootNode.findAccessibilityNodeInfosByViewId("com.whatsapp:id/menuitem_search")
                .ifEmpty { rootNode.findAccessibilityNodeInfosByText("Search") }

            if (searchNodes != null && searchNodes.isNotEmpty()) {
                val searchBtn = searchNodes[0]
                if (searchBtn.isClickable && searchBtn.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                    Log.i(TAG, "Clicked WhatsApp search button for contact '$contactName'")

                    // Wait 300ms for search input box
                    Handler(Looper.getMainLooper()).postDelayed({
                        val searchInput = rootInActiveWindow?.findAccessibilityNodeInfosByViewId("com.whatsapp:id/search_src_text")
                        if (searchInput != null && searchInput.isNotEmpty()) {
                            val arguments = Bundle().apply {
                                putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, contactName)
                            }
                            searchInput[0].performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
                            Log.i(TAG, "Entered contact name '$contactName' into search box")

                            // Wait 700ms for search results to load, then click contact in search results
                            Handler(Looper.getMainLooper()).postDelayed({
                                val clicked = clickSearchResultNode(contactName)
                                if (!clicked) {
                                    // Tap top result area at (0.5 * width, 0.25 * height) as fallback
                                    val metrics = resources.displayMetrics
                                    performTapGesture((metrics.widthPixels * 0.5f).toInt(), (metrics.heightPixels * 0.25f).toInt())
                                    Log.i(TAG, "Fallback tapped top search result item for '$contactName' ✓")
                                }
                                activePendingContactName = null
                            }, 700)
                        }
                    }, 300)
                    return true
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in performContactSearchAndSelect: ${e.message}")
        }
        return false
    }

    private fun clickSearchResultNode(contactName: String): Boolean {
        val root = rootInActiveWindow ?: return false

        // Strategy 1: Find node containing contactName
        val textNodes = root.findAccessibilityNodeInfosByText(contactName)
        if (textNodes != null && textNodes.isNotEmpty()) {
            for (node in textNodes) {
                if (clickNodeOrParent(node)) {
                    Log.i(TAG, "Clicked contact search result node by text '$contactName' ✓")
                    return true
                }
            }
        }

        // Strategy 2: Find contact container view IDs
        val ids = arrayOf(
            "com.whatsapp:id/contact_row_container",
            "com.whatsapp:id/contact_name",
            "com.whatsapp:id/contact_title",
            "com.whatsapp:id/conversations_row_contact_name",
            "com.whatsapp:id/contactselector_title"
        )
        for (id in ids) {
            val nodes = root.findAccessibilityNodeInfosByViewId(id)
            if (nodes != null && nodes.isNotEmpty()) {
                for (node in nodes) {
                    if (clickNodeOrParent(node)) {
                        Log.i(TAG, "Clicked contact search result node by view ID '$id' ✓")
                        return true
                    }
                }
            }
        }
        return false
    }

    private fun clickNodeOrParent(node: AccessibilityNodeInfo?): Boolean {
        if (node == null) return false
        if (node.isClickable && node.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
            return true
        }
        var parent = node.parent
        while (parent != null) {
            if (parent.isClickable && parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                return true
            }
            parent = parent.parent
        }
        return false
    }

    private fun performTapGesture(x: Int, y: Int) {
        val path = Path().apply {
            moveTo(x.toFloat(), y.toFloat())
        }
        val builder = GestureDescription.Builder()
        builder.addStroke(GestureDescription.StrokeDescription(path, 0, 100))
        dispatchGesture(builder.build(), null, null)
    }

    private fun searchAndClickSendNode(node: AccessibilityNodeInfo?): Boolean {
        if (node == null) return false

        val viewId = node.viewIdResourceName ?: ""
        val desc = node.contentDescription?.toString() ?: ""

        if (viewId.contains("send", ignoreCase = true) || desc.contains("send", ignoreCase = true)) {
            if (node.isClickable && node.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                Log.i(TAG, "Clicked WhatsApp Send Node: viewId=$viewId desc=$desc")
                return true
            }
            val parent = node.parent
            if (parent != null && parent.isClickable && parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                Log.i(TAG, "Clicked WhatsApp Send Parent Node: viewId=$viewId desc=$desc")
                return true
            }
        }

        for (i in 0 until node.childCount) {
            val child = node.getChild(i)
            if (searchAndClickSendNode(child)) {
                return true
            }
        }

        return false
    }

    override fun onInterrupt() {
        Log.w(TAG, "NexoGestureUnlockService interrupted")
    }

    fun performPatternGesture(patternSequence: String): Boolean {
        return performAutomatedUnlock("PATTERN", patternSequence)
    }

    fun performAutomatedUnlock(type: String, value: String): Boolean {
        try {
            val metrics: DisplayMetrics = resources.displayMetrics
            val width = metrics.widthPixels
            val height = metrics.heightPixels

            Log.i(TAG, "Performing lockscreen swipe up gesture...")
            performSwipeUp(width, height)
            return true
        } catch (e: Exception) {
            Log.e(TAG, "Error performing swipe up gesture: ${e.message}")
            return false
        }
    }

    private fun performSwipeUp(width: Int, height: Int) {
        val swipePath1 = Path().apply {
            moveTo(width * 0.5f, height * 0.75f)
            lineTo(width * 0.5f, height * 0.15f)
        }

        val builder1 = GestureDescription.Builder()
        builder1.addStroke(GestureDescription.StrokeDescription(swipePath1, 0, 250))
        dispatchGesture(builder1.build(), object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription)
                Log.d(TAG, "Swipe UP 1 completed successfully")
            }
        }, null)

        // 2nd Swipe UP at 350ms delay for Xiaomi MIUI / HyperOS keyguard
        Handler(Looper.getMainLooper()).postDelayed({
            val swipePath2 = Path().apply {
                moveTo(width * 0.5f, height * 0.75f)
                lineTo(width * 0.5f, height * 0.15f)
            }
            val builder2 = GestureDescription.Builder()
            builder2.addStroke(GestureDescription.StrokeDescription(swipePath2, 0, 250))
            dispatchGesture(builder2.build(), object : GestureResultCallback() {
                override fun onCompleted(gestureDescription: GestureDescription?) {
                    super.onCompleted(gestureDescription)
                    Log.d(TAG, "Swipe UP 2 completed successfully")
                }
            }, null)
        }, 350)
    }
}
