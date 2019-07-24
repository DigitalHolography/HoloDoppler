using System;
using System.Collections.Generic;
using System.Text;

namespace PhDemoCS.Data
{
    public interface ISource
    {
        Cine CurrentCine { get; }
    }
}
