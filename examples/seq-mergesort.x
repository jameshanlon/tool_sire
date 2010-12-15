port led : 0x00010600;
val LENGTH := 1500;
val THRESHOLD := 1000;
var a[LENGTH];

% Merge
proc merge(var a[], var b[], var c[], val la, val lb: int) is
  var i;
  var j;
  var k;
{ i:=0 
; j:=0 
; k:=0
; while i<la and j<lb do 
  { if(a[i] <= b[j])
    then 
    { c[k] := a[i] 
    ; i:=i+1 ; k:=k+1
    } 
    else 
    { c[k] := b[j]
    ; j:=j+1 ; k:=k+1
    }
  }
; if i<la then c[k] := a[i] else skip
; if j<lb then c[k] := b[j] else skip
}

% Merge sort
proc msort(var t, var n, var array[], var len) is
  var a[];
  var b[]; 
  var i;
  var j;
{ led ! 1
; if len > 1 then 
  { i := len / 2
  ; j := len - i
  ; a aliases array[0..]
  ; b aliases array[i..]
  ; msort(t, n/2, a, i)
  ; msort(t+(n/2), n/2, b, j)
  ; merge(a, b, array, i, j)
  }
  else skip
}

% Main
proc main() is
  var i;
{ for i:=0 to LENGTH-1 do 
    a[i] := LENGTH-i
; msort(0, NUMCORES, a, LENGTH)
}