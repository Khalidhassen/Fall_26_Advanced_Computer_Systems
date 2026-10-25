/* AI-assisted Project 2 setup helper. Run from an elevated x64 Developer
 * Command Prompt. Adds ONLY SeLockMemoryPrivilege to the current account.
 * Build: cl /nologo /W4 large_page_right.c advapi32.lib
 * Usage: large_page_right.exe --grant
 * Optional removal of this direct assignment: large_page_right.exe --remove
 * Sign out/in after a change. This does not itself allocate any large pages.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <ntsecapi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

static int fail(const char *where, DWORD error)
{
    fprintf(stderr, "%s failed: Windows error %lu\n", where, error);
    return 1;
}

int main(int argc, char **argv)
{
    HANDLE token = NULL;
    DWORD bytes = 0, error;
    TOKEN_USER *user = NULL;
    LSA_HANDLE policy = NULL;
    LSA_OBJECT_ATTRIBUTES attrs = {0};
    LSA_UNICODE_STRING right;
    NTSTATUS status;
    wchar_t name[] = L"SeLockMemoryPrivilege";
    int remove, result = 1;
    if (argc != 2 || (strcmp(argv[1], "--grant") && strcmp(argv[1], "--remove"))) {
        fprintf(stderr, "Usage: %s --grant | --remove\n", argv[0]);
        return 1;
    }
    remove = !strcmp(argv[1], "--remove");
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &token))
        return fail("OpenProcessToken", GetLastError());
    GetTokenInformation(token, TokenUser, NULL, 0, &bytes);
    error = GetLastError();
    if (error != ERROR_INSUFFICIENT_BUFFER) {
        CloseHandle(token);
        return fail("GetTokenInformation size", error);
    }
    user = (TOKEN_USER *)malloc(bytes);
    if (!user) { CloseHandle(token); return fail("malloc", ERROR_NOT_ENOUGH_MEMORY); }
    if (!GetTokenInformation(token, TokenUser, user, bytes, &bytes)) {
        fail("GetTokenInformation", GetLastError()); goto cleanup;
    }
    attrs.Length = sizeof(attrs);
    status = LsaOpenPolicy(NULL, &attrs,
        POLICY_LOOKUP_NAMES | POLICY_CREATE_ACCOUNT, &policy);
    if (status) { fail("LsaOpenPolicy (run as administrator)", LsaNtStatusToWinError(status)); goto cleanup; }
    right.Buffer = name;
    right.Length = (USHORT)(wcslen(name) * sizeof(wchar_t));
    right.MaximumLength = (USHORT)sizeof(name);
    if (remove)
        status = LsaRemoveAccountRights(policy, user->User.Sid, FALSE, &right, 1);
    else
        status = LsaAddAccountRights(policy, user->User.Sid, &right, 1);
    if (status) { fail("Update SeLockMemoryPrivilege", LsaNtStatusToWinError(status)); goto cleanup; }
    printf("%s SeLockMemoryPrivilege for the account running this program.\n",
        remove ? "Removed direct assignment of" : "Granted");
    puts("Save your work, then sign out of Windows and sign back in.");
    puts("No sign-out or restart has been triggered by this helper.");
    result = 0;
cleanup:
    if (policy) LsaClose(policy);
    free(user);
    CloseHandle(token);
    return result;
}
