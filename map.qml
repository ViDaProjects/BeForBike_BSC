import QtQuick
import QtLocation
import QtPositioning

// Root item
Item {
    width: 800
    height: 600
    Plugin {
        id: offlineOsm
        name: "osm"
        
        PluginParameter { 
            name: "osm.mapping.offline.directory";
            value: Qt.resolvedUrl("mapa_menor")
        } 
        
        PluginParameter { 
            name: "osm.mapping.offline.enabled";
            value: true 
        }
        // Adicione esta linha para garantir que o Qt não busque dados de roteamento online, etc.
        PluginParameter { name: "osm.mapping.providersrepository.disabled"; value: true }
        
    }
    // The Map component
    Map {
        id: map
        anchors.fill: parent
        plugin: offlineOsm



        // Center the map on the current position from the Python backend
        center: map_backend.currentPosition
        zoomLevel: 18 // Initial zoom

        // --- 1. The Path Polyline ---
        // This draws the recorded path
        MapPolyline {
            id: pathLine

            // Bind the 'path' property directly to our Python property
            path: map_backend.pathModel

            line.width: 4
            line.color: "blue"
        }

        // --- 2. The Current Position Marker ---
        // This shows a red circle at the current GPS location
        MapQuickItem {
            id: currentPosMarker

            // Bind the 'coordinate' property to our Python property
            coordinate: map_backend.currentPosition

            // Center the marker on the coordinate
            anchorPoint.x: sourceItem.width / 2
            anchorPoint.y: sourceItem.height / 2

            sourceItem: Rectangle {
                width: 16
                height: 16
                radius: 8
                color: "red"
                border.color: "white"
                border.width: 2
            }
        }
    }
}
