"""
Text-to-Speech Service
Converts text to audio using various TTS engines
"""

import os
import re
from typing import List, Optional, Callable
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment
import tempfile
from app.config import settings


class TTSService:
    """Handles text-to-speech conversion"""
    
    def __init__(self, engine: str = None):
        self.engine = engine or settings.TTS_ENGINE
        self.chunk_size = settings.TTS_CHUNK_SIZE
        self.language = settings.TTS_LANGUAGE
    
    def convert_to_audio(
        self,
        text: str,
        output_path: str,
        language: str = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> dict:
        """
        Convert text to audio file
        
        Args:
            text: Text to convert
            output_path: Path where audio file will be saved
            language: Language code (default: from settings)
            progress_callback: Optional callback function to report progress (0-100)
            
        Returns:
            Dictionary with audio file information
        """
        language = language or self.language
        
        # Split text into chunks for better processing
        chunks = self._split_text_into_chunks(text)
        total_chunks = len(chunks)
        
        # Generate audio for each chunk
        temp_files = []
        
        try:
            for i, chunk in enumerate(chunks):
                temp_file = self._generate_chunk_audio(chunk, language)
                temp_files.append(temp_file)
                
                # Report progress
                if progress_callback:
                    progress = int((i + 1) / total_chunks * 90)  # Up to 90%
                    progress_callback(progress)
            
            # Combine all audio chunks
            combined_audio = self._combine_audio_chunks(temp_files)
            
            # Save final audio
            combined_audio.export(output_path, format="mp3", bitrate="128k")
            
            # Final progress update
            if progress_callback:
                progress_callback(100)
            
            # Get audio metadata
            duration = len(combined_audio) / 1000.0  # Convert to seconds
            file_size = os.path.getsize(output_path)
            
            return {
                'file_path': output_path,
                'duration': duration,
                'file_size': file_size,
                'format': 'mp3'
            }
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into manageable chunks for TTS processing
        Tries to split at sentence boundaries
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence exceeds chunk size, save current chunk
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add remaining text
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _generate_chunk_audio(self, text: str, language: str) -> str:
        """
        Generate audio for a single text chunk
        Returns path to temporary audio file
        """
        if self.engine == "gtts":
            return self._generate_with_gtts(text, language)
        elif self.engine == "pyttsx3":
            return self._generate_with_pyttsx3(text, language)
        else:
            raise ValueError(f"Unsupported TTS engine: {self.engine}")
    
    def _generate_with_gtts(self, text: str, language: str) -> str:
        """Generate audio using Google Text-to-Speech"""
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3')
        os.close(temp_fd)
        
        try:
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(temp_path)
            return temp_path
        except Exception as e:
            os.remove(temp_path)
            raise Exception(f"gTTS conversion failed: {str(e)}")
    
    def _generate_with_pyttsx3(self, text: str, language: str) -> str:
        """Generate audio using pyttsx3 (offline)"""
        import pyttsx3
        
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3')
        os.close(temp_fd)
        
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Speed
            engine.setProperty('volume', 0.9)  # Volume
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            return temp_path
        except Exception as e:
            os.remove(temp_path)
            raise Exception(f"pyttsx3 conversion failed: {str(e)}")
    
    def _combine_audio_chunks(self, audio_files: List[str]) -> AudioSegment:
        """
        Combine multiple audio files into one
        Adds small silence between chunks
        """
        if not audio_files:
            raise ValueError("No audio files to combine")
        
        # Load first audio
        combined = AudioSegment.from_mp3(audio_files[0])
        
        # Add silence between chunks (100ms)
        silence = AudioSegment.silent(duration=100)
        
        # Combine all audio files
        for audio_file in audio_files[1:]:
            audio = AudioSegment.from_mp3(audio_file)
            combined = combined + silence + audio
        
        return combined
    
    def estimate_duration(self, text: str, words_per_minute: int = 150) -> float:
        """
        Estimate audio duration based on text length
        
        Args:
            text: Input text
            words_per_minute: Average speaking rate
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        duration_minutes = word_count / words_per_minute
        return duration_minutes * 60