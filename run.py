import asyncio
import time
import wave
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from io import BytesIO
import whisper

from app.agent.lerobot import Lerobot
from app.flow.base import FlowType
from app.flow.flow_factory import FlowFactory
from app.logger import logger

class SpeechRecognizer:  
    def __init__(self):  
        self.model = whisper.load_model("base")  
        self.fs = 16000  
        self.channels = 1  
        self.input_device = 5  # 确认设备索引正确  
        self.dtype = "float32"  # 明确指定数据类型  

    def _record_chunk(self, duration=5):  
        """返回形状为 (samples,) 的音频数据"""  
        recording = sd.rec(  
            int(duration * self.fs),  
            samplerate=self.fs,  
            channels=self.channels,  
            device=self.input_device,  
            dtype=self.dtype,  # 显式指定类型  
            blocking=True,  
        )  
        return recording.squeeze()  # 关键修复：压缩为单通道一维数组  

    async def continuous_recognition(self):  
        try:  
            logger.info("Microphone ready, start listening...")  
            while True:  
                # 获取音频数据（形状已修正为 (samples,)）  
                audio_data = await asyncio.get_event_loop().run_in_executor(  
                    None, self._record_chunk, 5  
                )  

                # 验证数据格式  
                if audio_data.dtype != np.float32:  
                    audio_data = audio_data.astype(np.float32)  
                
                # 关键参数设置  
                result = await asyncio.get_event_loop().run_in_executor(  
                    None,   
                    lambda: self.model.transcribe(  
                        audio_data,  
                        language="zh",  
                        fp16=False,  
                        no_speech_threshold=0.3    
                    )  
                )  
                
                text = result["text"].strip()  
                if text:  
                    logger.info(f"recognition result: {text}")  
                    yield text  
        except Exception as e:  
            logger.error(f"Speech recognition failed: {str(e)}")  
            raise  

async def run_flow(recognizer):
    agents = {
        "lerobot": Lerobot(),
    }

    try:
        async for prompt in recognizer.continuous_recognition():
            if not prompt:
                continue
            flow = FlowFactory.create_flow(
                flow_type=FlowType.PLANNING,
                agents=agents,
            )
            logger.warning("Processing your request...")

            try:
                start_time = time.time()
                result = await asyncio.wait_for(
                    flow.execute(prompt),
                    timeout=3600,
                )
                elapsed_time = time.time() - start_time
                logger.info(f"Request processed in {elapsed_time:.2f} seconds")
                logger.info(result)
            except asyncio.TimeoutError:
                logger.error("Request processing timed out after 1 hour")
                logger.info("Operation timed out. Please try a simpler request.")

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    recognizer = SpeechRecognizer()
    
    # 设备验证
    try:
        sd.check_input_settings(
            device=recognizer.input_device,
            samplerate=recognizer.fs,
            channels=recognizer.channels
        )
    except sd.PortAudioError as e:
        logger.error(f"Device incompatibility: {str(e)}")
        logger.info("Please select from the following valid input devices：")
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                logger.info(f"Index {i}: {dev['name']}")
        exit(1)
    
    sd.default.device = recognizer.input_device
    sd.default.samplerate = recognizer.fs
    sd.default.channels = recognizer.channels
    
    asyncio.run(run_flow(recognizer))