# PRD (R05 rewrite) — cd021eac3c93ed0d2de1

- Domain: BIO
- Job to be done: read and write biosignal files
- Blocker: file reading/writing, format conversion or parameter handling fails
- Score: 70 (corrected R03/R04 scoring; see score_reason below)
- Score reason: E=20 (3 indep orgs, 13 distinct authors, 16 raw URLs) job='read and write biosignal files' S=20 (blocker 'file reading/writing, format conversion or parameter handling fails' matches failure keywords ['fails']) F=15 (recorded workaround exists ('see linked issues'); feasibility indicated but NOT validated — F capped at 15 of 20 max) G=10 (checked 2 alternatives, none fully solves (see competitor_checks)) L=5 (no transfer/reuse evidence in record; L capped at 5 (minimum) — no cross-domain reuse claim made) | cross-org corroborated
- Independent organisations: 3; VERIFIED evidence: 16 links (8 closed, 8 open)

## User task
As a researcher working with biosignal files, read a WFDB, EDF or FIFF file and write it back without the data changing and without the operation crashing.

## Evidence (VERIFIED sources only, with quotations/paraphrases)
- [open] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/515
  - calc_adc_params can produce off-by-one problems, crashing wrsamp
  - Quoted/paraphrased from the post: "I have some data that crashes `wrsamp` because `calc_adc_params` produces values that don't fit the data (off by one): ``` chmin = -2147483648 chmax = 2147483648 IndexError: Channel 0 contain values outside allowed range [-2147483648, 2147483647] for fmt 32 ``` As you can see, `chmax` is _just ab..."
- [open] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/522
  - OverflowError with rdann on LUED annotations w/numpy 2.2
  - Quoted/paraphrased from the post: "Another area of incompatibility with numpy 2.2 I fear... If I try ```python wfdb.rdann('physionet.org/files/ludb/1.0.0/1', extension='atr_ii') ``` or (for version 1.0.1) ```python wfdb.rdann('physionet.org/files/ludb/1.0.1/1', extension='ii') ``` I get: ``` ---------------------------------------..."
- [closed] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/524
  - OverflowError on wfdb.rdann()
  - Quoted/paraphrased from the post: "I am trying to read annotations from [NSRDB](https://physionet.org/content/nsrdb/1.0.0/) like this: ``` >>> import wfdb >>> wfdb.rdann("nsrdb/16265", "atr") ``` I keep getting the following error: ``` Traceback (most recent call last): File "<stdin>", line 1, in <module> File "/home/marty/Documen..."
- [open] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/528
  - HeaderSyntaxError encountered when processing the PTB-XL+ database
  - Quoted/paraphrased from the post: "WFDB version: 4.1.2 header file: https://physionet.org/content/ptb-xl-plus/1.0.1/median_beats/12sl/00000/00001_medians.hea header file content: ```text ge_median_beats_wfdb/00001_medians 12 500 600 ge_median_beats_wfdb/00001_medians.dat 32 6344117.125(-1842966025)/mV 32 0 -1995224836 10742 0 I ge..."
- [open] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/534
  - Use a single `path` argument (and deprecate `pn_dir` and `file_name`)
  - Quoted/paraphrased from the post: "Currently the WFDB API uses 2 arguments to specify the location of files: `pn_dir` and `file_name`. This is confusing for users and confusing for developers (e.g. see: https://github.com/MIT-LCP/wfdb-python/pull/523/files). I think the reason for having two arguments is to support auto-detection ..."
- [closed] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/543
  - Problem using record.wrsamp()
  - Quoted/paraphrased from the post: "Hello, I trying to save a Record but when usin record.wrsamp(write_dir=str(directory)), it requests some optional parameters like checksum. After defining them i get the following error: path/src/python/utils/__init__.py:9: UserWarning: Module tf_keras not found, some of the submodules cannot be ..."
- [closed] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/547
  - Update README or documentation to explain how to access WFDB files from cloud URIs
  - Quoted/paraphrased from the post: "As I see in the different commits and issues, the support to access WFDB files from cloud URIs has been added since a while, however, I'm not able to find information on how to do it in the documentation. Could you please add the needed command to do it? If you can also integrate it with addition..."
- [open] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/554
  - wfdb.io.MultiRecord.wrsamp missing option for expanded=True
  - Quoted/paraphrased from the post: "wfdb.io.MultiRecord.wrsamp (which just calls 'self.wrheader' and then 'for seg in self.segments: seg.wrsamp') seems to be missing the ability to pass 'expanded=True', as one can with wfdb.io.Record.wrsamp. This causes checksums to fail as the checks look for things related to 'd_signal' rather th..."
- [open] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/568
  - Authentication handling in wfdb.io.dl_files, error 403
  - Quoted/paraphrased from the post: "# Context I am trying to download specific **files (subsets)** from credentialed databases on PhysioNet using wfdb helper functions. What I am trying to do is downloading selected files (not the entire dataset), e.g. : ``` from wfdb.io import dl_files dl_files('mimiciv','data\\tmp',['hosp/patient..."
- [closed] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/593
  - csv_to_wfdb mishandles defaults, scalar broadcasting and checksums
  - Quoted/paraphrased from the post: "Found while reviewing #591. The code in `csv_to_wfdb` that fills in defaults and broadcasts scalars to all channels (https://github.com/MIT-LCP/wfdb-python/blob/b8914e1c9c777c45571c894cb7b6579550a86f13/src/wfdb/io/convert/csv.py#L338-L409) has several problems: - Scalars are only broadcast when `..."
- [closed] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/594
  - csv_to_wfdb docstring has incorrect parameter descriptions
  - Quoted/paraphrased from the post: "Found while reviewing #591, which fixes the summary, `record_only`, `write_dir` and return value descriptions. Some other parameter descriptions in the `csv_to_wfdb` docstring are wrong, mostly because they were copied from elsewhere: - `file_name` is copied from `rdrecord`. It says the name is g..."
- [closed] [MIT-LCP/wfdb-python] https://github.com/MIT-LCP/wfdb-python/issues/618
  - Record.wrsamp() fails with a TypeError when the record has no d_signal
  - Quoted/paraphrased from the post: "`Record.wrsamp()` fails with an unhelpful error for a record read with the default `physical=True`: ```python import wfdb record = wfdb.rdrecord("sample-data/100", sampto=1000) record.wrsamp(write_dir="out") # TypeError: unsupported operand type(s) for %: 'NoneType' and 'int' ``` The record only ..."
- [open] [mne-tools/mne-python] https://github.com/mne-tools/mne-python/issues/14428
  - Proposal: correctness benchmark + reviewed skill files for AI assistants (outside core)
  - Quoted/paraphrased from the post: "Hi all, AI assistants and MNE keep coming up, both here and on the forum. I went back through the earlier discussions and wanted to suggest something concrete that I think addresses the concerns raised there. **What's been discussed so far** - #13288: the Steering Council decided not to promote a..."
- [closed] [mne-tools/mne-python] https://github.com/mne-tools/mne-python/issues/14431
  - mne-bids cannot find split files saved with split_naming="bids" when the name has desc
  - Quoted/paraphrased from the post: "### Description of the problem `split_naming="bids"` (in `Raw.save` and `Epochs.save`) inserts `split-XX` just before the suffix: https://github.com/mne-tools/mne-python/blob/8f498626a53704a6a96bcd8a11e22cbd8866efa5/mne/_fiff/utils.py#L322-L335 mne-bids on the other hand does it differently. Orde..."
- [open] [mne-tools/mne-python] https://github.com/mne-tools/mne-python/issues/14460
  - `read_forward_solution` loses subcortical source spaces
  - Quoted/paraphrased from the post: "### Description of the problem A forward solution built from a subcortical surface source space (`setup_subcortical_source_space, added in #14130) doesn't survive a write/read round trip. The issue seems to be here: https://github.com/mne-tools/mne-python/blob/main/mne/forward/forward.py#L610-L61..."
- [closed] [neuropsychology/NeuroKit] https://github.com/neuropsychology/NeuroKit/issues/1162
  - NeuroKit not working with Pandas 3
  - Quoted/paraphrased from the post: "I haven't made a comprehensive test of the full suite, but the EDA processing portion is not working with Pandas 3.0 which was released last month. It uses the `DataFrame.pad` function that has been depreciated since Pandas 2.0 and has finally been removed: ``` File "C:\work\git\DADS-analysis\.ve..."

## Actual workaround and impact
No workaround is documented in the record. Reporters describe the failure and file it; wfdb #547 asks for documentation on how to access WFDB files from cloud URIs, which is a documentation gap, not a workaround for the read/write failures.

Read/write failures in the evidence: calc_adc_params produces off-by-one values that crash wrsamp with an IndexError on values at the int32 bounds (wfdb #515); rdann raises OverflowError on LUED annotations with numpy 2.2 (#522) and on NSRDB annotations (#524); a HeaderSyntaxError is raised processing the PTB-XL+ database headers (#528); Record.wrsamp() fails with a TypeError when the record has no d_signal (#618); csv_to_wfdb mishandles defaults, scalar broadcasting and checksums (#593); read_forward_solution loses subcortical source spaces on a write/read round trip (MNE #14460).

## Competitor checks (R04, checked 2026-11-05, 0 solve the pain)
- MNE-Python (1.13.2) — https://mne.tools/stable/index.html (checked 2026-11-05)
  - Observed capability: MNE docs: 'MNE 1.13.2 documentation' - EEG/MEG data I/O and analysis. HTTP 200, 2026-11-05.
  - Gap vs this pain: Heavy dependency and limited format coverage; and the reported file I/O failures are partly filed against MNE itself, so it does not fix its own failures.
- pyEDFlib (v0.1.42) — https://github.com/holgern/pyedflib (checked 2026-11-05)
  - Observed capability: GitHub repo: 'pyedflib is a python library to read/write EDF+/BDF+ files based on EDFli...' HTTP 200, 2026-11-05.
  - Gap vs this pain: EDF+/BDF+ only; file reading/writing, format conversion and parameter-handling failures for other biosignal formats remain.

## Sample input
Two recorded reproducers. (1) wfdb #515: a record with chmin=-2147483648 and chmax=2147483648, written with wrsamp. (2) wfdb #618: wfdb.rdrecord('sample-data/100', sampto=1000) followed by record.wrsamp(write_dir='out').

## Expected output
(1) wrsamp completes and the ADC parameters fit the data — no off-by-one, no IndexError. (2) wrsamp on a record with no d_signal either writes successfully or raises a clear error naming the missing signal — never a TypeError about '%' formatting on NoneType.

## Acceptance tests
1. wrsamp on the #515 boundary record (chmin=-2147483648, chmax=2147483648) completes, and a re-read of the written record returns values inside the int32 range.
2. rdrecord('sample-data/100', sampto=1000) followed by wrsamp() from #618 does not raise TypeError; either it writes, or it reports 'no d_signal' explicitly.
3. rdann on the #522 LUED annotation file with numpy 2.2 returns annotations without OverflowError.
4. A forward solution built with a subcortical source space survives a write/read round trip with the subcortical space intact (#14460).
5. csv_to_wfdb with scalar-per-channel defaults broadcasts the scalar to every channel and writes matching checksums (#593).

## Caveats and stop conditions
- 8 of 16 VERIFIED evidence items are CLOSED — closed does not mean solved.
- Two items inside the theme are adjacent, not file-I/O failures: #534 (a proposal to replace pn_dir/file_name with a single path argument) and #547 (a documentation request for cloud URIs).
- The theme spans 3 organisations (wfdb, MNE, NeuroKit) with 13 distinct authors; the round-trip case (#14460) is MNE-specific and the ADC case (#515) is wfdb-specific, so an MVP must prove one of them on its own library's reproducer.
- Closed evidence items are counted as evidence of a real problem, not as proof the problem is solved: R02 did not check resolution from comments.
- If the linked sources are withdrawn or the blocker is fixed upstream, this PRD is withdrawn.
