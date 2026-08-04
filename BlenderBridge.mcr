macroScript BlenderBridgeToggle
category:"Ali Assiri Tools"
toolTip:"Blender Connection Manager 🔗"
buttonText:"Blender Toggle"
(
    global blenderBridgeActive
    global blenderListenerTimer
    global blenderBridgeRollout
    
    -- دالة إنهاء الاتصال وتنظيف الواجهة
    fn closeBlenderBridge = 
    (
        blenderBridgeActive = false
        try (destroyDialog blenderBridgeRollout) catch()
        
        -- حذف ملف الجسر من النظام لقطع الاتصال من جهة بلندر أيضاً
        local bridge_file = sysInfo.tempdir + "blender_max_bridge.json"
        if doesFileExist bridge_file do (deleteFile bridge_file)
        
        print "Blender Bridge Disconnected & Closed! 🔴"
        messageBox "تم إنهاء الاتصال بنجاح وتوقف المراقبة." title:"Blender Bridge"
    )

    -- إذا كان متصلاً مسبقاً، قم بإغلاق الاتصال
    if blenderBridgeActive == true then
    (
        closeBlenderBridge()
    )
    else
    (
        -- إذا لم يكن متصلاً، افتح الاتصال وبدأ المراقبة
        blenderBridgeActive = true
        
        try (destroyDialog blenderBridgeRollout) catch()
        
        -- تعريف الواجهة (Rollout) مع النصوص العربية المحدثة
        rollout blenderBridgeRollout "Blender Connection Manager" width:250 height:90
        (
            -- نصوص عربية واضحة (تم التأكد من الترميز)
            label lbl_status "الحالة: جاري الاتصال والمراقبة... 🟢" pos:[10,15] width:230 height:20
            button btn_toggle_conn "إنهاء الاتصال (Disconnect) ❌" pos:[10,45] width:230 height:35
            
            timer t interval:1000 active:true
            global lastExportTime = ""
            
            -- زر الإنهاء اليدوي من داخل النافذة
            on btn_toggle_conn pressed do
            (
                closeBlenderBridge()
            )
            
            -- مراقبة التحديثات من بلندر
            on t tick do 
            (
                if blenderBridgeActive == true then
                (
                    local bridge_file = sysInfo.tempdir + "blender_max_bridge.json"
                    
                    -- التأكد من بقاء ملف الاتصال نشطاً
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
                            
                            -- استيراد ملف الـ OBJ
                            importFile f #noPrompt using:OBJ
                            
                            -- تعديل حجم المجسمات الجديدة ليطابق المتر تماماً
                            local newObjects = for obj in (getCurrentSelection()) where (findItem oldSelection obj == 0) collect obj
                            if newObjects.count > 0 then
                            (
                                for obj in newObjects do
                                (
                                    obj.scale = obj.scale * 1000.0
                                )
                            )
                            
                            -- حذف ملف الـ OBJ المؤقت لضمان استقبال التصديرات القادمة
                            try (deleteFile f) catch()
                            
                            print "Model Auto-Imported & Scaled Successfully! 🚀"
                            lbl_status.text = "الحالة: تم استيراد المجسم بنجاح! 🎯"
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
        
        -- تفعيل ملف الاتصال الفوري
        local bridge_file = sysInfo.tempdir + "blender_max_bridge.json"
        local f = openFile bridge_file mode:"w"
        format "{\n  \"status\": \"active\"\n}" to:f
        close f
        
        createDialog blenderBridgeRollout 250 90 style:#(#style_toolwindow, #style_sysmenu, #style_minimizebox)
        print "Blender Bridge Opened & Connected! 🟢"
    )
)