#ifndef MD_RETRY132
#define MD_RETRY132
// Volatile acquisition schedule, separate from every operational/protection deadline.
// First 600s: 30s retries. Afterwards: bounded 120s probes of the SAME rejected window.
struct MDRetry132 {bool active,slow;long from,end,started,next;int failures;};
void MDReset132(MDRetry132 &r){r.active=false;r.slow=false;r.from=0;r.end=0;r.started=0;r.next=0;r.failures=0;}
bool MDExpired132(const MDRetry132 &r,long now){return r.active&&(now<r.started||now-r.started>=600000);}
bool MDSlow132(const MDRetry132 &r,long now){return r.active&&(r.slow||(now>=r.started&&now-r.started>=600000));}
bool MDEnterSlow132(MDRetry132 &r,long now)
{if(!r.active||r.slow||now<r.started||now-r.started<600000)return false;r.slow=true;r.next=now+120000;return true;}
bool MDDue132(const MDRetry132 &r,long now){return !r.active||(now>=r.started&&now>=r.next);}
bool MDFail132(MDRetry132 &r,long from,long end,long now)
{
 if(!r.active){r.active=true;r.slow=false;r.from=from;r.end=end;r.started=now;r.failures=0;}
 if(r.from!=from||r.end!=end||now<r.started)return false;
 r.slow=MDSlow132(r,now);r.failures++;r.next=now+(r.slow?120000:30000);return true;
}
// Age alone never proves validity. Caller must verify complete data, identity and connection.
bool MDCanCommit132(const MDRetry132 &r,long from,long end,long now)
{return !r.active||(r.from==from&&r.end==end&&now>=r.started);}
#endif
