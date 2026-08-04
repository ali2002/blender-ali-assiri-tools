macroScript AliBlenderBridgeNew
category:"Ali Assiri Tools"
toolTip:"Ali Blender Bridge"
buttonText:"Ali Blender Bridge"
(
    global blenderBridgeActive
    global blenderListenerTimer
    global blenderBridgeRollout
    
    -- Close connection and clean up UI
    fn closeBlenderBridge = 
    (
        blenderBridgeActive = false
        try (destroyDialog blenderBridgeRollout) catch()
        
        -- Delete the bridge file to fully stop the Blender-side connection
        local bridge_file = sysInfo.tempdir + "blender_max_bridge.json"
        if doesFileExist bridge_file do (deleteFile bridge_file)
        
        print "Blender Bridge Disconnected and Closed."
        messageBox "Connection closed successfully. Monitoring stopped." title:"Ali Blender Bridge"
    )

    -- If already connected, close the connection
    if blenderBridgeActive == true then
    (
        closeBlenderBridge()
    )
    else
    (
        -- If not connected, start connection and monitoring
        blenderBridgeActive = true
        
        try (destroyDialog blenderBridgeRollout) catch()
        
        -- Define the rollout UI
        rollout blenderBridgeRollout "Ali Blender Bridge" width:250 height:90
        (
            label lbl_status "Status: Connected and monitoring..." pos:[10,15] width:230 height:20
            button btn_toggle_conn "Disconnect" pos:[10,45] width:230 height:35
            
            timer t interval:1000 active:true
            global lastExportTime = ""
            
            -- Manual disconnect button inside the dialog
            on btn_toggle_conn pressed do
            (
                closeBlenderBridge()
            )
            
            -- Monitor updates from Blender
            on t tick do 
            (
                if blenderBridgeActive == true then
                (
                    local bridge_file = sysInfo.tempdir + "blender_max_bridge.json"
                    
                    -- Ensure the bridge status file remains active
                    if not (doesFileExist bridge_file) then
                    (
                        local f = openFile bridge_file mode:"w"
                        format "{\n  \"status\": \"active\"\n}" to:f
                        close f
                    )
                    
                    local f = sysInfo.tempdir + "blender_export.obj"
                    if doesFileExist f then 
                    (
                        local mTime = getFileCreateDate f
                        if mTime != lastExportTime do 
                        (
                            lastExportTime = mTime
                            
                            local oldSelection = getCurrentSelection()
                            
                            -- Import OBJ file
                            importFile f #noPrompt using:OBJ
                            
                            -- Scale newly imported objects to match meter-based scale
                            local newObjects = for obj in (getCurrentSelection()) where (findItem oldSelection obj == 0) collect obj
                            if newObjects.count > 0 then
                            (
                                for obj in newObjects do
                                (
                                    obj.scale = obj.scale * 1000.0
                                )
                            )
                            
                            -- Remove temp OBJ to allow future exports
                            try (deleteFile f) catch()
                            
                            print "Model auto-imported and scaled successfully."
                            lbl_status.text = "Status: Model imported successfully."
                        )
                    )
                )
            )
            
            on blenderBridgeRollout close do
            (
                blenderBridgeActive = false
                local bridge_file = sysInfo.tempdir + "blender_max_bridge.json"
                if doesFileExist bridge_file do (deleteFile bridge_file)
            )
        )
        
        -- Create bridge status file immediately
        local bridge_file = sysInfo.tempdir + "blender_max_bridge.json"
        local f = openFile bridge_file mode:"w"
        format "{\n  \"status\": \"active\"\n}" to:f
        close f
        
        createDialog blenderBridgeRollout 250 90 style:#(#style_toolwindow, #style_sysmenu, #style_minimizebox)
        print "Blender Bridge Opened and Connected."
    )
)