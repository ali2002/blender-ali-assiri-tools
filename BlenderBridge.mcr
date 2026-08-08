macroscript AliBlenderBridgeNew
category:"Ali Tools"
toolTip:"Ali Blender Bridge"
buttonText:"Ali Blender Bridge"
(
    global blenderBridgeActive
    global blenderBridgeRollout
    
    local sharedDir = "C:\\AliBridge\\"
    
    fn closeBlenderBridge = 
    (
        blenderBridgeActive = false
        try (destroyDialog blenderBridgeRollout) catch()
        local bridge_file = sharedDir + "blender_max_bridge.json"
        if doesFileExist bridge_file do (deleteFile bridge_file)
        print "Bridge Disconnected."
        messageBox "Connection closed." title:"Ali Tools"
    )

    if blenderBridgeActive == true then closeBlenderBridge()
    else
    (
        blenderBridgeActive = true
        try (destroyDialog blenderBridgeRollout) catch()
        
        rollout blenderBridgeRollout "Ali Blender Bridge & Tools" width:250 height:200
        (
            label lbl_status "Status: Connected..." pos:[10,12] width:230 height:20
            button btn_match_name "Match Position & Rotation" pos:[10,40] width:230 height:35
            button btn_manual_import "Import Latest OBJ Now" pos:[10,85] width:230 height:30
            button btn_toggle_conn "Disconnect" pos:[10,125] width:230 height:35
            
            timer t interval:1000 active:true
            global lastExportTime = ""
            
            on btn_match_name pressed do
            (
                local bridge_file = sharedDir + "blender_max_bridge.json"
                if doesFileExist bridge_file then
                (
                    try (
                        local f = openFile bridge_file mode:"r"
                        local content = readline f
                        close f
                        
                        local name_match = (dotnetClass "System.Text.RegularExpressions.Regex").Match content "\"full_name\":\"([^\"]+)\""
                        local target_name = (name_match.Groups.Item 1).Value
                        
                        local loc_match = (dotnetClass "System.Text.RegularExpressions.Regex").Match content "\"location\":\\[([0-9.-]+),([0-9.-]+),([0-9.-]+)\\]"
                        local rot_match = (dotnetClass "System.Text.RegularExpressions.Regex").Match content "\"rotation\":\\[([0-9.-]+),([0-9.-]+),([0-9.-]+)\\]"
                        
                        if target_name != "" and loc_match.Success and rot_match.Success then (
                            local px = ((loc_match.Groups.Item 1).Value as float) * 1000.0
                            local py = ((loc_match.Groups.Item 2).Value as float) * 1000.0
                            local pz = ((loc_match.Groups.Item 3).Value as float) * 1000.0
                            
                            local rx = (rot_match.Groups.Item 1).Value as float
                            local ry = (rot_match.Groups.Item 2).Value as float
                            local rz = (rot_match.Groups.Item 3).Value as float
                            
                            local found_obj = getNodeByName target_name
                            if found_obj != undefined then (
                                found_obj.pos = [px, py, pz]
                                found_obj.rotation = (eulerAngles rx ry rz)
                                messageBox ("تم تطبيق الموقع والدوران للمجسم: " + found_obj.name) title:"Ali Tools"
                            ) else (
                                messageBox ("لم يتم العثور على مجسم باسم: " + target_name) title:"تنبيه"
                            )
                        ) else (
                            messageBox "خطأ في قراءة بيانات الموقع والدوران من الملف." title:"خطأ"
                        )
                    ) catch (
                        messageBox "حدث خطأ أثناء معالجة ملف البيانات." title:"خطأ"
                    )
                ) else (
                    messageBox "ملف البيانات غير موجود في C:\\AliBridge\\" title:"تنبيه"
                )
            )
            
            on btn_manual_import pressed do
            (
                local f = sharedDir + "blender_export.obj"
                if doesFileExist f then (
                    local oldSelection = getCurrentSelection()
                    importFile f #noPrompt using:OBJ
                    local newObjects = for obj in (getCurrentSelection()) where (findItem oldSelection obj == 0) collect obj
                    if newObjects.count > 0 then (
                        for obj in newObjects do ( 
                            obj.scale = obj.scale * 1000.0 
                            -- تحويل كافة العناصر المستوردة يدوياً إلى Edit Poly بدقة
                            try (convertTo obj Editable_Poly) catch()
                        )
                    )
                    messageBox "All imported models converted to Editable Poly!" title:"Ali Tools"
                ) else (
                    messageBox "لا يوجد ملف OBJ في C:\\AliBridge\\" title:"تنبيه"
                )
            )

            on btn_toggle_conn pressed do closeBlenderBridge()
            
            on t tick do 
            (
                if blenderBridgeActive == true then
                (
                    if not (doesDirectoryExist sharedDir) then makeDir sharedDir
                    local f = sharedDir + "blender_export.obj"
                    if doesFileExist f then 
                    (
                        local mTime = getFileCreateDate f
                        if mTime != lastExportTime do 
                        (
                            lastExportTime = mTime
                            local oldSelection = getCurrentSelection()
                            importFile f #noPrompt using:OBJ
                            local newObjects = for obj in (getCurrentSelection()) where (findItem oldSelection obj == 0) collect obj
                            if newObjects.count > 0 then
                            (
                                for obj in newObjects do 
                                ( 
                                    obj.scale = obj.scale * 1000.0 
                                    -- تحويل كافة العناصر المستوردة تلقائياً عبر التايمر إلى Edit Poly
                                    try (convertTo obj Editable_Poly) catch()
                                )
                            )
                            try (deleteFile f) catch()
                            lbl_status.text = "Status: Imported & converted to Edit Poly."
                        )
                    )
                )
            )
            
            on blenderBridgeRollout close do ( blenderBridgeActive = false )
        )
        createDialog blenderBridgeRollout 250 200 style:#(#style_toolwindow, #style_sysmenu, #style_minimizebox)
        print "Bridge Connected."
    )
)