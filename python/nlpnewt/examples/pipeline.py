# Copyright 2019 Regents of the University of Minnesota.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""An example pipeline."""

import sys

import nlpnewt

TEXT_COLUMN = 1

ID_COLUMN = 0


@nlpnewt.processor('example-pipeline')
def create_pipeline():
    pipeline = nlpnewt.Pipeline()

    pipeline.add_processor('nlpnewt-example-processor-python')
    pipeline.add_processor('nlpnewt-example-processor-java')

    return pipeline


if __name__ == '__main__':
    import sqlite3
    from datetime import datetime
    from time import time

    file = sys.argv[1]
    conn = sqlite3.connect(file)
    c = conn.cursor()
    source_documents = c.execute('SELECT * FROM txts').fetchall()

    print("Starting....")
    start_time = datetime.now()

    with nlpnewt.Events() as events, nlpnewt.Pipeline() as pipeline:
        pipeline.add_processor('nlpnewt-example-processor-python', params={'do_work': True})
        pipeline.add_processor('nlpnewt-example-processor-java', params={'do_work': True})
        for i, row in enumerate(source_documents):
            source_id = str(row[ID_COLUMN])
            source_text = str(row[TEXT_COLUMN])
            with events.open_event(source_id) as event:
                event.metadata['source'] = 'example pipeline'
                doc = event.add_document('plaintext', source_text)
                pipeline.run(doc)

        pipeline.print_times()

    total_time = datetime.now() - start_time
    print(f"Total time: {total_time}")
