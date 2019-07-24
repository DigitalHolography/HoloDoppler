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
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////

using System;
using System.Collections.Generic;
using System.Text;
using System.Windows.Forms;


namespace PhSharp
{
    public static class ErrorHandler
    {
        /// <summary>
        /// Form from which modal dialog is shown
        /// </summary>
        public static Form zMainForm;

        private static HRESULT zLastErrorCode;
        public static HRESULT LastErrorCode
        {
            get { return zLastErrorCode; }
            private set { zLastErrorCode = value; }
        }

        private static string zLastMessage;
        public static string LastMessage
        {
            get { return zLastMessage; }
            private set { zLastMessage = value; }
        }

        public static bool IsConnectionError(HRESULT result)
        {
            //
            // no longer want to see timeout error with new enumeration (06/16/2017)
            //
            return (result == HRESULT.ERR_NoResponseFromCamera || result == HRESULT.ERR_TimeOut
                    || result == HRESULT.ERR_GetImageTimeOut || result == HRESULT.ERR_BadCameraNumber);
        }

        public static void CheckError(HRESULT errCode)
        {
            LastErrorCode = errCode;
            LastMessage = "";
            if (errCode != 0)
            {
                string errorMessage = GetErrorMessage(errCode);
                LastMessage = errorMessage;
                if (errCode < 0 
                    //
                    // a serious error was signaled
                    // in this demo we are not interested in these errors: ERR_BadTriggerTime, ERR_BadImageInterval and ERR_NotIncreasingTime
                    //
                    && errCode != HRESULT.ERR_BadImageInterval
                    && errCode != HRESULT.ERR_BadTriggerTime
                    && errCode != HRESULT.ERR_NotIncreasingTime

                    //
                    // no longer want to see timeout error with new enumeration (06/16/2017)
                    //
                    && errCode != HRESULT.ERR_GetTimeTimeOut
                    && errCode != HRESULT.ERR_NoResponseFromCamera
                    && errCode != HRESULT.ERR_GetAudioTimeOut
                    && errCode != HRESULT.ERR_TimeOut
                    && errCode != HRESULT.ERR_GetImageTimeOut)
                {
                    //alternatively you can use: throw new Exception(errorMessage);
                    MessageBox.Show(zMainForm, errorMessage, "PhError", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        public static void ThrowError(HRESULT errCode)
        {
            LastErrorCode = errCode;
            LastMessage = "";
            if (errCode != 0)
            {
                string errorMessage = GetErrorMessage(errCode);
                LastMessage = errorMessage;
                if (errCode < 0)
                    throw new Exception(errorMessage);
            }
        }

        public static string GetErrorMessage(HRESULT code)
        {
            StringBuilder errorMessageBuilder = new StringBuilder(PhCon.MAXSTDSTRSZ);
            PhCon.PhGetErrorMessage((int)code, errorMessageBuilder);
            if (code < 0)
                errorMessageBuilder.Insert(0, "Error: ");
            else if (code > 0)
                errorMessageBuilder.Insert(0, "Warning: ");

            return errorMessageBuilder.ToString();
        }
    }
}
