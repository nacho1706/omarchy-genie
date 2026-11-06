import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import "dock" as NativeDock
import qs.Commons

Item {
    id: root
    property var shell: null
    property var manifest: null
    property var settings: ({})
    property var userConfig: ({})
    property var defaultConfig: ({})
    property var clients: []
    property var monitors: []
    property var active: ({})
    property var snapshots: ({})
    readonly property bool busy: worker.running || screens.instances.some(function(s) { return s.capturing || s.animating })
    property var lastTarget: null
    property var lastAnimation: null
    property string error: ""
    property var completion: null
    readonly property string position: nativeDock.position
    readonly property int duration: Math.max(100, Math.min(1200, Number(settings.duration) || 520))
    readonly property real intensity: Math.max(0.2, Math.min(4, Number(settings.intensity) || 1.5))
    readonly property string adapter: Qt.resolvedUrl("tools/windows.py").toString().replace("file://", "")

    function refresh() { if (!poll.running) poll.running = true }
    function command(action, address, callback) {
        if (worker.running) return false
        completion = callback || null
        worker.command = ["python3", adapter, action, address || ""]
        worker.running = true
        return true
    }
    function showSettings() { var windows = screens.instances; for (var i = 0; i < windows.length; ++i) if (windows[i].monitor && windows[i].monitor === Hyprland.focusedMonitor) windows[i].settingsOpen = true }
    function dockTarget(screen, address) {
        var window = nativeDock.dockOn(screen)
        return window ? window.genieTarget(address) : null
    }
    function restoreAddress(address) {
        var c = clients.find(function(c) { return c.address === address && root.isMinimized(c) })
        if (!c) return false
        restore(c)
        return true
    }
    function minimizeAddress(address) {
        if (busy) return
        var c = clients.find(function(c) { return c.address === address })
        if (!c) { refresh(); return }
        var windows = screens.instances
        for (var i = 0; i < windows.length; ++i)
            if (windows[i].monitorId === c.monitor) { windows[i].minimize(c); return }
    }
    function minimize() {
        if (!busy && !activeQuery.running) activeQuery.running = true
    }
    Process {
        id: activeQuery
        command: ["hyprctl", "activewindow", "-j"]
        stdout: StdioCollector {
            onStreamFinished: { try { var c = JSON.parse(text); if (c.address) root.minimizeAddress(c.address) } catch(e) { root.error = String(e) } }
        }
    }
    function restoreLast() {
        var list = clients.filter(function(c) { return root.isMinimized(c) })
        list.sort(function(a,b) { return root.order(b) - root.order(a) })
        if (list.length) restore(list[0])
    }
    function order(c) {
        var tag = (c.tags || []).find(function(t) { return /^genie-order-\d+$/.test(t) })
        return tag ? Number(tag.substring(12)) : 0
    }
    function isMinimized(c) { return c.workspace.name === "special:minimized" && order(c) > 0 }
    function restore(c) {
        if (busy) return
        var windows = screens.instances
        for (var i = 0; i < windows.length; ++i)
            if (windows[i].monitorId === c.monitor) { windows[i].restore(c); return }
        command("restore", c.address)
    }
    function save(key, value) {
        var next = Object.assign({}, settings); next[key] = value
        if (shell) shell.updateEntryInline("chato.genie", next)
    }
    FileView {
        id: config
        path: (Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config") + "/omarchy/shell.json"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                var data = JSON.parse(text())
                root.userConfig = data
                var candidates = (data.plugins || []).slice()
                var layout = data.bar && data.bar.layout ? data.bar.layout : ({})
                Object.keys(layout).forEach(function(section) { if (Array.isArray(layout[section])) candidates = candidates.concat(layout[section]) })
                root.settings = candidates.find(function(p) { return p && p.id === "chato.genie" }) || ({})
            } catch(e) { root.error = "Cannot read Genie settings: " + e }
        }
    }
    FileView {
        path: "/usr/share/omarchy/config/omarchy/shell.json"
        onLoaded: { try { root.defaultConfig = JSON.parse(text()) } catch(e) {} }
    }
    QtObject {
        id: dockFacade
        property var shellConfig: root.userConfig
        property var defaultsConfig: root.defaultConfig
        property var appLibrary: root.shell ? root.shell.appLibrary : null
    }
    NativeDock.Dock { id: nativeDock; shell: dockFacade; genie: root }
    Process {
        id: poll
        command: ["python3", root.adapter, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var data = JSON.parse(text)
                    if (!data.clients) return
                    root.clients = data.clients; root.monitors = data.monitors; root.active = data.active
                    var alive = {}; data.clients.forEach(function(c) { if (root.snapshots[c.address]) alive[c.address] = root.snapshots[c.address] })
                    root.snapshots = alive
                } catch(e) { root.error = String(e) }
            }
        }
    }
    Process {
        id: worker
        property var result: ({})
        stdout: StdioCollector { onStreamFinished: { try { worker.result = JSON.parse(text) } catch(e) { worker.result = {error: String(e)} } } }
        onExited: function(code, status) {
            var cb = root.completion; root.completion = null
            root.error = result.error || ""
            if (cb) cb(code === 0 && !result.error)
            Qt.callLater(root.refresh)
        }
    }
    Timer { interval: 750; repeat: true; running: true; triggeredOnStart: true; onTriggered: root.refresh() }
    Connections { target: Hyprland; function onRawEvent(event) { if (event.name === "activewindowv2") root.refresh() } }
    ShellIpc {
        target: "chato.genie"
        function status(): string { return JSON.stringify({duration: root.duration, intensity: root.intensity, position: root.position, target: root.lastTarget, animation: root.lastAnimation, error: root.error, busy: root.busy}) }
        function configure(json: string): void {
            try {
                var input = JSON.parse(json), next = Object.assign({}, root.settings)
                if (typeof input.duration === "number" && isFinite(input.duration)) next.duration = Math.max(100, Math.min(1200, input.duration))
                if (typeof input.intensity === "number" && isFinite(input.intensity)) next.intensity = Math.max(0.2, Math.min(4, input.intensity))
                if (root.shell) root.shell.updateEntryInline("chato.genie", next)
            } catch(e) { root.error = String(e) }
        }
        function activateDock(address: string): void {
            var items = nativeDock.items
            for (var i = 0; i < items.length; ++i) {
                var w = items[i].windows.find(function(w) { return String(w.address).replace(/^0x/, "") === address.replace(/^0x/, "") })
                if (w) { nativeDock.bringForward(w); return }
            }
        }
        function minimize(): void { root.minimize() }
        function minimizeAddress(address: string): void { root.minimizeAddress(address) }
        function restoreLast(): void { root.restoreLast() }
        function settings(): void { root.showSettings() }
        function hideSettings(): void { var windows = screens.instances; for (var i = 0; i < windows.length; ++i) windows[i].settingsOpen = false }
    }
    Variants {
        id: screens
        model: Quickshell.screens
        delegate: Component { GenieScreen { required property var modelData; screen: modelData; controller: root } }
    }
}
