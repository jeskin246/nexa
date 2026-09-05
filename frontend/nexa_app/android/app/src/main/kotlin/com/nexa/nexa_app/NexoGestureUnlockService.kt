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
            if (now - lastClickTime < 1500) return

            attemptWhatsAppSendWithRetry()
        }
    }

    private var isProcessingContact = false

    private fun attemptWhatsAppSendWithRetry() {
        val handler = Handler(Looper.getMainLooper())

        // If we have a pending contact name to search & select, handle that first
        val pendingContact = activePendingContactName
        if (!pendingContact.isNullOrEmpty() && !isProcessingContact) {
            isProcessingContact = true
            handler.postDelayed({
                performContactSearchAndSelect(pendingContact)
            }, 300)
            return
        }

        val delays = listOf(100L, 400L, 900L, 1600L, 2500L, 3800L, 5000L)
        for (delay in delays) {
            handler.postDelayed({
                val clicked = autoClickWhatsAppSendButton()
                if (clicked) {
                    lastClickTime = System.currentTimeMillis()
                    Log.i(TAG, "WhatsApp Send button successfully clicked! ✓")
                }
            }, delay)
        }
    }

    private fun autoClickWhatsAppSendButton(): Boolean {
        val rootNode = rootInActiveWindow ?: return false
        try {
            // Strategy 1: Find by resource ID (com.whatsapp:id/send or com.whatsapp.w4b:id/send or fab)
            val sendIds = arrayOf("com.whatsapp:id/send", "com.whatsapp.w4b:id/send", "com.whatsapp:id/fab", "com.whatsapp:id/send_btn")
            for (id in sendIds) {
                val nodes = rootNode.findAccessibilityNodeInfosByViewId(id)
                if (nodes != null && nodes.isNotEmpty()) {
                    for (node in nodes) {
                        if (clickNodeOrParent(node)) {
                            Log.i(TAG, "Successfully auto-clicked WhatsApp Send button by View ID ($id) ✓")
                            return true
                        }
                    }
                }
            }

            // Strategy 2: Find by Content Description ("Send", "send", "Next")
            val sendDescriptions = arrayOf("Send", "send", "Send message", "Next")
            for (desc in sendDescriptions) {
                val nodes = rootNode.findAccessibilityNodeInfosByText(desc)
                if (nodes != null && nodes.isNotEmpty()) {
                    for (node in nodes) {
                        if (clickNodeOrParent(node)) {
                            Log.i(TAG, "Successfully auto-clicked WhatsApp Send button by Text ($desc) ✓")
                            return true
                        }
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

    private fun performContactSearchAndSelect(contactName: String) {
        val handler = Handler(Looper.getMainLooper())
        val rootNode = rootInActiveWindow
        if (rootNode == null) {
            isProcessingContact = false
            return
        }

        try {
            // Check if search input is already open
            val directInput = rootNode.findAccessibilityNodeInfosByViewId("com.whatsapp:id/search_src_text")
            if (directInput != null && directInput.isNotEmpty()) {
                val arguments = Bundle().apply {
                    putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, contactName)
                }
                directInput[0].performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
                Log.i(TAG, "Entered contact name '$contactName' into visible search box ✓")
                scheduleSearchResultSelection(contactName)
                return
            }

            // Find and click search button icon
            val searchBtnIds = arrayOf(
                "com.whatsapp:id/menuitem_search",
                "com.whatsapp:id/search_button",
                "com.whatsapp:id/action_search",
                "com.whatsapp:id/search_holder",
                "com.whatsapp:id/search_icon"
            )
            var clickedSearch = false
            for (id in searchBtnIds) {
                val nodes = rootNode.findAccessibilityNodeInfosByViewId(id)
                if (nodes != null && nodes.isNotEmpty()) {
                    if (clickNodeOrParent(nodes[0])) {
                        clickedSearch = true
                        Log.i(TAG, "Clicked WhatsApp search button by ID ($id) ✓")
                        break
                    }
                }
            }

            if (!clickedSearch) {
                val searchTexts = arrayOf("Search", "Search contacts", "Search…")
                for (txt in searchTexts) {
                    val nodes = rootNode.findAccessibilityNodeInfosByText(txt)
                    if (nodes != null && nodes.isNotEmpty()) {
                        if (clickNodeOrParent(nodes[0])) {
                            clickedSearch = true
                            Log.i(TAG, "Clicked WhatsApp search button by Text ($txt) ✓")
                            break
                        }
                    }
                }
            }

            // Wait 350ms for search input to animate, then type text
            handler.postDelayed({
                val currentRoot = rootInActiveWindow
                val searchInput = currentRoot?.findAccessibilityNodeInfosByViewId("com.whatsapp:id/search_src_text")
                    ?: currentRoot?.findAccessibilityNodeInfosByText("Search")
                if (searchInput != null && searchInput.isNotEmpty()) {
                    val arguments = Bundle().apply {
                        putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, contactName)
                    }
                    searchInput[0].performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
                    Log.i(TAG, "Entered contact name '$contactName' into search box ✓")
                }
                scheduleSearchResultSelection(contactName)
            }, 350)

        } catch (e: Exception) {
            Log.e(TAG, "Error in performContactSearchAndSelect: ${e.message}")
            isProcessingContact = false
        }
    }

    private fun scheduleSearchResultSelection(contactName: String) {
        val handler = Handler(Looper.getMainLooper())
        // Wait 600ms for search results to render
        handler.postDelayed({
            val clicked = clickSearchResultNode(contactName)
            if (!clicked) {
                // Fallback tap top search result item at (0.5 * width, 0.22 * height)
                val metrics = resources.displayMetrics
                performTapGesture((metrics.widthPixels * 0.5f).toInt(), (metrics.heightPixels * 0.22f).toInt())
                Log.i(TAG, "Fallback tapped top search result item for '$contactName' ✓")
            }

            // After selecting contact, if on Contact Picker, tap green Next / Send FAB button
            handler.postDelayed({
                clickContactPickerFabOrSend()
                activePendingContactName = null
                isProcessingContact = false

                // Try tapping final send button inside opened chat with progressive retries
                val sendDelays = listOf(500L, 1000L, 1800L, 2800L, 4000L)
                for (d in sendDelays) {
                    handler.postDelayed({
                        val sent = autoClickWhatsAppSendButton()
                        if (sent) {
                            lastClickTime = System.currentTimeMillis()
                            Log.i(TAG, "Successfully tapped final WhatsApp send button in opened chat! ✓")
                        }
                    }, d)
                }
            }, 500)
        }, 600)
    }

    private fun clickContactPickerFabOrSend(): Boolean {
        val root = rootInActiveWindow ?: return false
        val fabIds = arrayOf("com.whatsapp:id/fab", "com.whatsapp:id/send", "com.whatsapp:id/next_btn", "com.whatsapp:id/send_btn")
        for (id in fabIds) {
            val nodes = root.findAccessibilityNodeInfosByViewId(id)
            if (nodes != null && nodes.isNotEmpty()) {
                if (clickNodeOrParent(nodes[0])) {
                    Log.i(TAG, "Clicked Contact Picker Forward/Send FAB by ID ($id) ✓")
                    return true
                }
            }
        }
        val descs = arrayOf("Send", "Next", "Forward")
        for (d in descs) {
            val nodes = root.findAccessibilityNodeInfosByText(d)
            if (nodes != null && nodes.isNotEmpty()) {
                if (clickNodeOrParent(nodes[0])) {
                    Log.i(TAG, "Clicked Contact Picker Forward/Send FAB by Text ($d) ✓")
                    return true
                }
            }
        }
        // Fallback tap bottom-right corner for FAB
        val metrics = resources.displayMetrics
        performTapGesture((metrics.widthPixels * 0.88f).toInt(), (metrics.heightPixels * 0.92f).toInt())
        return true
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
            "com.whatsapp:id/conversations_row_contact_name",
            "com.whatsapp:id/contact_name",
            "com.whatsapp:id/contact_title",
            "com.whatsapp:id/contactselector_title",
            "com.whatsapp:id/contact_picker_row",
            "com.whatsapp:id/contact_item"
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
            Log.i(TAG, "Clicked node via ACTION_CLICK ✓")
            return true
        }
        var parent = node.parent
        while (parent != null) {
            if (parent.isClickable && parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                Log.i(TAG, "Clicked parent node via ACTION_CLICK ✓")
                return true
            }
            parent = parent.parent
        }

        // Physical Screen Touch Gesture using exact bounding box coordinates
        val rect = android.graphics.Rect()
        node.getBoundsInScreen(rect)
        if (!rect.isEmpty && rect.centerX() > 0 && rect.centerY() > 0 && rect.centerY() < resources.displayMetrics.heightPixels) {
            performTapGesture(rect.centerX(), rect.centerY())
            Log.i(TAG, "Dispatched physical screen tap at (${rect.centerX()}, ${rect.centerY()}) for node ✓")
            return true
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
