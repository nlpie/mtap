/*
 * Copyright 2019 Regents of the University of Minnesota.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package main

import (
	"fmt"
	"io/ioutil"
	"os"
	"strings"
)

func main() {
	dir := os.Args[1]
	fs, _ := ioutil.ReadDir(dir)
	out, _ := os.Create(dir + "/swaggers.go")
	_, err := out.Write([]byte("package mtap_api_v1 \n\nconst (\n"))
	if err != nil {
		print(err)
		panic(err)
	}
	for _, f := range fs {
		if strings.HasSuffix(f.Name(), ".json") {
			swagger, err := ioutil.ReadFile(dir + "/" + f.Name())
			swaggerString := string(swagger)

			name := strings.TrimSuffix(f.Name(), ".swagger.json")
			name = strings.ToUpper(name[0:1]) + name[1:]
			_, err = fmt.Fprintf(out, "%s = %q \n", name, swaggerString)
			if err != nil {
				print(err)
				panic(err)
			}
		}
	}
	_, err = out.Write([]byte(")\n"))
	if err != nil {
		print(err)
		panic(err)
	}
}
