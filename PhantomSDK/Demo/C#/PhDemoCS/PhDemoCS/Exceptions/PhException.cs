using System;
using System.Collections.Generic;
using System.Text;
using PhSharp;


namespace PhDemoCS.Exceptions
{
    public class PhException : Exception
    {
        int zErrorCode;
        public int ErrorCode
        {
            get { return this.zErrorCode; }
            private set { this.zErrorCode = value; }
        }

        public PhException(int errorCode, string message)
            : base(message)
        {
            ErrorCode = errorCode;
        }
    }
}
