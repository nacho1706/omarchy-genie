import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import qs.Commons
import qs.Commons as Commons

Item {
    id: root
    required property var screen
    required property var controller
    readonly property var monitor: Hyprland.monitorFor(screen)
    readonly property int monitorId: monitor ? monitor.id : -1
    readonly property bool vertical: controller.position === "left" || controller.position === "right"
    readonly property var entries: controller.clients.filter(function(c) { return c.monitor === root.monitorId && controller.isMinimized(c) }).sort(function(a,b) { return controller.order(a) - controller.order(b) })
    readonly property bool fullscreen: controller.clients.some(function(c) { return root.monitor && root.monitor.activeWorkspace && c.workspace.id === root.monitor.activeWorkspace.id && c.fullscreen >= 2 })
    property var pending: null
    property var captureTarget: null
    property var afterAnimation: null
    readonly property bool animating: motion.running
    property bool capturing: false
    property bool settingsOpen: false
    readonly property int dockOffset: 76

    function targetRect(address) {
        return controller.dockTarget(root.screen, address)
    }
    function play(c, image, reverse, done) {
        afterAnimation = done
        controller.lastAnimation = {phase: reverse ? "restore" : "minimize", animated: false, reason: !image ? "capture unavailable" : "animations disabled", at: Date.now()}
        if (!image || Style.duration(controller.duration) === 0) { if (done) done(); afterAnimation = null; return }
        picture.source = image.url
        effect.sourceRect = Qt.vector4d(c.at[0] - monitor.x, c.at[1] - monitor.y, c.size[0], c.size[1])
        var destination = targetRect(c.address)
        if (!destination) { controller.lastAnimation = {phase: reverse ? "restore" : "minimize", animated: false, reason: "dock target unavailable", at: Date.now()}; if (done) done(); afterAnimation = null; return }
        controller.lastTarget = {x: destination.x, y: destination.y, width: destination.z, height: destination.w}
        effect.targetRect = destination
        motion.from = reverse ? 1 : 0; motion.to = reverse ? 0 : 1
        controller.lastAnimation = {phase: reverse ? "restore" : "minimize", animated: true, at: Date.now()}
        motion.start()
    }
    function minimize(c) {
        if (capturing || motion.running || controller.completion) return
        if (!c.floating || c.fullscreen || c.workspace.id < 1) return
        pending = c
        var top = Hyprland.toplevels.values.find(function(t) { return ("0x" + String(t.address).replace(/^0x/, "")) === c.address })
        if (!top || !top.wayland) { finishCapture(null); return }
        captureTarget = top.wayland
        capturing = true
        captureTimeout.start()
    }
    function finishCapture(image) {
        captureTimeout.stop(); capturing = false
        var c = pending; pending = null
        if (!c) return
        if (image) { var next = Object.assign({}, controller.snapshots); next[c.address] = image; controller.snapshots = next }
        controller.command("minimize", c.address, function(ok) { if (ok) play(c, image, false, null) })
    }
    function restore(c) {
        if (motion.running || capturing) return
        play(c, controller.snapshots[c.address], true, function() { controller.command("restore", c.address) })
    }
    Timer { id: captureTimeout; interval: 250; onTriggered: root.finishCapture(null) }
    PanelWindow {
        id: overlay
        screen: root.screen
        anchors { top: true; bottom: true; left: true; right: true }
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "omarchy-genie-animation"
        mask: Region {}
        visible: root.capturing || motion.running
        Loader {
            active: root.capturing
            sourceComponent: Component {
                ScreencopyView {
                    x: -width - 1
                    width: root.pending ? root.pending.size[0] : 1
                    height: root.pending ? root.pending.size[1] : 1
                    captureSource: root.captureTarget
                    live: false
                    paintCursor: false
                    onHasContentChanged: {
                        if (hasContent && root.capturing) grabToImage(function(result) { if (root.capturing) root.finishCapture(result) })
                    }
                }
            }
        }
        Image { id: picture; visible: false }
        ShaderEffect {
            id: effect
            anchors.fill: parent
            property var source: picture
            property vector4d sourceRect
            property vector4d targetRect
            property real progress: 0
            property real intensity: controller.intensity
            property real edge: controller.position === "bottom" ? 0 : controller.position === "top" ? 1 : controller.position === "right" ? 2 : 3
            mesh: GridMesh { resolution: Qt.size(64,64) }
            vertexShader: Qt.resolvedUrl("shaders/genie.vert.qsb")
            fragmentShader: Qt.resolvedUrl("shaders/genie.frag.qsb")
        }
        NumberAnimation {
            id: motion; target: effect; property: "progress"
            duration: Style.duration(controller.duration)
            easing.type: Easing.InOutCubic
            onFinished: { var cb = root.afterAnimation; root.afterAnimation = null; if (cb) cb() }
        }
    }
    PanelWindow {
        id: preferences
        screen: root.screen
        color: "transparent"
        visible: root.settingsOpen
        anchors { bottom: controller.position === "bottom"; top: controller.position === "top"; left: controller.position === "left"; right: controller.position === "right" }
        implicitWidth: root.settingsOpen ? 340 : root.vertical ? 64 : Math.min(root.screen.width, (root.entries.length + 2) * 52 + 12)
        implicitHeight: root.settingsOpen ? 300 : root.vertical ? Math.min(root.screen.height, (root.entries.length + 2) * 52 + 12) : 64
        margins { bottom: controller.position === "bottom" ? root.dockOffset : 0; top: controller.position === "top" ? root.dockOffset : 0; left: controller.position === "left" ? root.dockOffset : 0; right: controller.position === "right" ? root.dockOffset : 0 }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Top
        WlrLayershell.namespace: "omarchy-genie-settings"
        Rectangle {
            anchors.fill: parent; radius: Style.cornerRadius; color: Commons.Color.popups.background
            border.color: Commons.Color.popups.text; border.width: 1
            Column {
                visible: root.settingsOpen; anchors.centerIn: parent; spacing: 8; width: 300
                Text { text: "Genie"; color: Commons.Color.popups.text; textFormat: Text.PlainText }
                Text { text: "Target: Omarchy dock"; textFormat: Text.PlainText; color: Commons.Color.popups.text }
                Text { text: "Duration: " + controller.duration + " ms"; textFormat: Text.PlainText; color: Commons.Color.popups.text }
                Slider { width: 280; from: 100; to: 1200; stepSize: 20; value: controller.duration; onMoved: controller.save("duration", Math.round(value)) }
                Text { text: "Intensity"; textFormat: Text.PlainText; color: Commons.Color.popups.text }
                Slider { width: 280; from: 0.2; to: 4; value: controller.intensity; onMoved: controller.save("intensity", value) }
                Text { width: 290; wrapMode: Text.Wrap; text: controller.error.substring(0, 240); visible: text.length > 0; textFormat: Text.PlainText; color: Commons.Color.urgent }
                Button { text: "Close"; onClicked: root.settingsOpen = false }
            }
        }
    }
}
