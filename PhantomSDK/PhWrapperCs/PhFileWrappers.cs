//////////////////////////////////////////////////////////////////////////////////
//  Copyright (C) 1992-2019                                                     //
//       Vision Research Inc. (An AMETEK Company) All Rights Reserved.          //
//                                                                              //
//  The licensed information contained herein is the property of                //
//  Vision Research Inc., Wayne, NJ, USA  and is subject to change              //
//  without notice.                                                             //
//                                                                              //
//  Redistribution and use in source and binary forms, with or without          //
//  modification, are permitted with the following conditions.                  //
//                                                                              //
//  THIS SOFTWARE IS PROVIDED BY VISION RESEARCH INC ``AS IS'' AND              //
//  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE       //
//  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE  //
//  ARE DISCLAIMED.  IN NO EVENT SHALL VISION RESEARCH INC BE LIABLE            //
//  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL  //
//  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS     //
//  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)       //
//  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT  //
//  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY   //
//  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF      //
//  SUCH DAMAGE.                                                                //
//                                                                              //
//  Updates:                                                                    //
//              June 28, 2017   Updated for 770 SDK Release                     //
//              July 20, 2017   Updated for 770 SDK Release                     //
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////

using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;



namespace PhSharp
{
    public static class PhFileWrappers
    {
        public static int GetCineInfoIntegerValue(IntPtr cineHandle, CineInfo selector)
        {
            int InfVal;
            ErrorHandler.CheckError
                (PhFile.PhGetCineInfo(cineHandle, selector, out InfVal));
            return InfVal;
        }

        public static void SetCineInfoIntegerValue(int value, IntPtr cineHandle, CineInfo selector)
        {
            ErrorHandler.CheckError
                (PhFile.PhSetCineInfo(cineHandle, selector, ref value));
        }

        public static float GetCineInfoFloatValue(IntPtr cineHandle, CineInfo selector)
        {
            IntPtr pFloatValue = new IntPtr();
            pFloatValue = Marshal.AllocHGlobal(sizeof(float));
            ErrorHandler.CheckError(
                PhFile.PhGetCineInfo(cineHandle, selector, pFloatValue));
            float value = UtilMemory.GetFloatValueFromIntPtr(pFloatValue);
            Marshal.FreeHGlobal(pFloatValue);
            return value;
        }

        public static void SetCineInfoFloatValue(float value, IntPtr cineHandle, CineInfo selector)
        {
            IntPtr pFloatValue = new IntPtr();
            pFloatValue = Marshal.AllocHGlobal(sizeof(float));
            UtilMemory.SetFloatValueToIntPtr(value, ref pFloatValue);
            ErrorHandler.CheckError(
                PhFile.PhSetCineInfo(cineHandle, selector, pFloatValue));
            Marshal.FreeHGlobal(pFloatValue);
        }

        public static WBGain GetCineInfoWB(IntPtr ch, CineInfo wbSelection)
        {
            if (!(wbSelection == CineInfo.GCI_WB || wbSelection == CineInfo.GCI_WBVIEW))
                throw new Exception("Not a WB selection");

            WBGain wb = new WBGain();
            IntPtr pWB = new IntPtr();
            pWB = Marshal.AllocHGlobal(Marshal.SizeOf(wb));
            ErrorHandler.CheckError(
                PhFile.PhGetCineInfo(ch, wbSelection, pWB));
            wb = (WBGain)Marshal.PtrToStructure(pWB, typeof(WBGain));
            Marshal.FreeHGlobal(pWB);
            return wb;
        }

        public static HRESULT GetCineInfoWB(IntPtr ch, CineInfo wbSelection, ref WBGain wb)
        {
            if (!(wbSelection == CineInfo.GCI_WB || wbSelection == CineInfo.GCI_WBVIEW))
                throw new Exception("Not a WB selection");

            IntPtr pWB = new IntPtr();
            pWB = Marshal.AllocHGlobal(Marshal.SizeOf(wb));
            HRESULT result = PhFile.PhGetCineInfo(ch, wbSelection, pWB);
            wb = (WBGain)Marshal.PtrToStructure(pWB, typeof(WBGain));
            Marshal.FreeHGlobal(pWB);
            return result;
        }

        public static void SetCineInfoWB(WBGain wb, IntPtr ch, CineInfo wbSelection)
        {
            if (!(wbSelection == CineInfo.GCI_WB || wbSelection == CineInfo.GCI_WBVIEW))
                throw new Exception("Not a WB selection");

            IntPtr pWB = Marshal.AllocHGlobal(Marshal.SizeOf(wb));
            Marshal.StructureToPtr(wb, pWB, true);
            ErrorHandler.CheckError(
                PhFile.PhSetCineInfo(ch, wbSelection, pWB));
            Marshal.FreeHGlobal(pWB);
        }

        public static HRESULT SetCineInfoWB(IntPtr ch, CineInfo wbSelection, WBGain wb)
        {
            if (!(wbSelection == CineInfo.GCI_WB || wbSelection == CineInfo.GCI_WBVIEW))
                throw new Exception("Not a WB selection");

            IntPtr pWB = Marshal.AllocHGlobal(Marshal.SizeOf(wb));
            Marshal.StructureToPtr(wb, pWB, true);
            HRESULT result = PhFile.PhSetCineInfo(ch, wbSelection, pWB);
            Marshal.FreeHGlobal(pWB);
            return result;
        }

        /// <summary>
        /// Show a dialog for cine browsing.
        /// </summary>
        /// <param name="options">Selection capabilities of the dialog.</param>
        /// <param name="startFilePath">Set the folder where to start browsing.</param>
        /// <returns>True if the selection terminated witk OK.</returns>
        public static bool GetOpenCineName(OFN options, string startFilePath, out string retunedFilePath)
        {
            bool dialogResult = false;
            retunedFilePath = "";

            if (options == OFN.SINGLESELECT)
            {
                const int bytesToAlloc = PhFile.MAX_MULTI_PATH;
                IntPtr pFileName = Marshal.AllocHGlobal(bytesToAlloc);
                if (!string.IsNullOrEmpty(startFilePath))
                {
                    UtilMemory.CopyStringToPointerAnsi(startFilePath, pFileName);
                }
                //show open cine dialog
                dialogResult = PhFile.PhGetOpenCineName(pFileName, options);

                retunedFilePath = Marshal.PtrToStringAnsi(pFileName);
                Marshal.FreeHGlobal(pFileName);
            }
            else
                //in this demo MultiSelection is not available, MultiSelect can be used for batch convert.
                throw new NotImplementedException();

            return dialogResult;
        }

        public static HRESULT SetCineInfoSaveRange(IntPtr ch, ImRange imRange)
        {
            IntPtr pImRange = Marshal.AllocHGlobal(Marshal.SizeOf(imRange));
            Marshal.StructureToPtr(imRange, pImRange, true);
            HRESULT result = PhFile.PhSetCineInfo(ch, CineInfo.GCI_SAVERANGE, pImRange);
            Marshal.FreeHGlobal(pImRange);
            return result;
        }

        public static HRESULT SetCineInfoSaveFileName(IntPtr ch, SaveFileName saveFileName)
        {
            IntPtr pFileName = Marshal.AllocHGlobal(Marshal.SizeOf(saveFileName));
            Marshal.StructureToPtr(saveFileName, pFileName, true);
            HRESULT result = PhFile.PhSetCineInfo(ch, CineInfo.GCI_SAVEFILENAME, pFileName);
            Marshal.FreeHGlobal(pFileName);
            return result;
        }


    }
}
