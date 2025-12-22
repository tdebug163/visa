import os
import sys
import time
import subprocess
import signal

# قائمة لتتبع العمليات الفرعية
active_processes = {}

def run_script(script_name):
    """
    تشغل ملف بايثون كعملية منفصلة وتتبعها.
    """
    print(f"🚀 جاري تشغيل {script_name}...")
    try:
        # استخدام sys.executable لضمان استخدام نفس مفسر بايثون
        # Popen يجعل العملية غير محظورة (non-blocking)
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        active_processes[script_name] = process
        print(f"✅ {script_name} تم تشغيله بنجاح (معرف العملية: {process.pid})")
        return process
    except FileNotFoundError:
        print(f"❌ خطأ: الملف {script_name} غير موجود.")
        return None
    except Exception as e:
        print(f"❌ فشل في تشغيل {script_name}: {e}")
        return None

def restart_script(script_name):
    """
    إعادة تشغيل سكربت معين إذا توقف.
    """
    if script_name in active_processes:
        process = active_processes[script_name]
        if process.poll() is not None: # تحقق إذا كانت العملية قد توقفت
            print(f"🔄 إعادة تشغيل {script_name} لأنه توقف...")
            new_process = run_script(script_name)
            if new_process:
                active_processes[script_name] = new_process
            return True
    return False

def monitor_processes():
    """
    مراقبة العمليات الفرعية وإعادة تشغيلها إذا توقفت.
    """
    while True:
        time.sleep(10)  # فحص كل 10 ثواني
        
        # إعادة تشغيل visa.py إذا توقف
        restart_script('visa.py')
        
        # إعادة تشغيل crvisa.py إذا توقف
        restart_script('crvisa.py')

def cleanup(signum, frame):
    """
    تنظيف العمليات عند إيقاف التطبيق.
    """
    print("\n🛑 استلام إشارة إيقاف... جاري إغلاق جميع العمليات الفرعية.")
    for script_name, process in active_processes.items():
        try:
            print(f"🛑 إيقاف {script_name} (PID: {process.pid})...")
            process.terminate()
            process.wait(timeout=5)
        except Exception as e:
            print(f"❌ فشل في إيقاف {script_name}: {e}")
    sys.exit(0)

if __name__ == '__main__':
    # التحقق من وجود توكن البوت
    if not os.environ.get('TG_BOT_VISA'):
        print("خطأ: متغير البيئة TG_BOT_VISA غير موجود.")
        sys.exit(1)
        
    print("========================================")
    print("   بدء تشغيل مكونات التطبيق...")
    print("========================================")
    
    # تسجيل معالج إشارة الإيقاف (Ctrl+C)
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # تشغيل البوت (ملف visa.py)
    run_script('visa.py')
    
    # تشغيل مولد البطاقات (ملف crvisa.py)
    run_script('crvisa.py')
    
    print("\n========================================")
    print("   تم إطلاق المكونات بنجاح.")
    print("   الآن يمكنك استخدام الأوامر في تيليجرام.")
    print("   المراقبة تعمل في الخلفية لإعادة تشغيل أي مكون يتوقف.")
    print("========================================")
    
    # تشغيل المراقبة في الخلفية
    # هذه الدالة لن تنتهي، مما يبقي main.py نشطًا
    try:
        monitor_processes()
    except KeyboardInterrupt:
        cleanup(None, None)
    except Exception as e:
        print(f"🚨 حدث خطأ في المراقبة: {e}")
        cleanup(None, None)